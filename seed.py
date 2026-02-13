from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
import random

import pandas as pd
from django.utils import timezone
from django.db import transaction

from charges.models import Charge
from patients.models import Patient
from payments.models import Payment
from staff.models import Staff
from lab_requests.models import LabObservation, LabTest, LabRequest, LabTestRequest
from visits.models import Visit
from vital_signs.models import VitalSign
from physical_exams.models import PhysicalExam


def _parse_decimal(value):
    if value is None or pd.isna(value): # pd.isna catches more variants of null
        return Decimal('0.00') # Return zero instead of None to prevent math errors
    try:
        s = str(value).strip()
        if s == '' or s.lower() == 'nan':
            return Decimal('0.00')
        return Decimal(s)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0.00')

@transaction.atomic
def seed_db():
    random.seed(42)

    # Create a few staff users used as creators/orderers
    def _ensure_staff(username, role, password='password'):
        user, created = Staff.objects.get_or_create(username=username, defaults={'role': role})
        if created:
            user.set_password(password)
            user.save()
        return user

    admin = _ensure_staff('admin', Staff.RoleEnum.ADMIN)
    doctor = _ensure_staff('dr_jane', Staff.RoleEnum.DOCTOR)
    labtech = _ensure_staff('lab_tech', Staff.RoleEnum.LABORATORY)
    reception = _ensure_staff('Sami', Staff.RoleEnum.RECEPTION)

    # Seed test groups
    groups_df = pd.read_csv('seed_data/mock-test-groups.csv')
    tests = []
    for _, row in groups_df.iterrows():
        price = _parse_decimal(row.get('price')) or Decimal('0.00')
        test, _ = LabTest.objects.get_or_create(
            name=row.get('name') or 'Unnamed',
            defaults={'price': price, 'created_by': admin}
        )
        tests.append(test)

    if not tests:
        # fallback: create one group
        t = LabTest.objects.create(name='Default', price=Decimal('0.00'), created_by=admin)
        tests.append(t)

    # Seed tests
    observations_df = pd.read_csv('seed_data/mock-tests.csv')
    observations = []
    type_map = {
        'NUMERICAL': LabObservation.ResultTypeEnum.NUMERICAL,
        'CATEGORICAL': LabObservation.ResultTypeEnum.CATEGORICAL,
        'NUMERIC': LabObservation.ResultTypeEnum.NUMERICAL,
    }
    for _, row in observations_df.iterrows():
        price = _parse_decimal(row.get('price'))
        ref_min = _parse_decimal(row.get('reference_min'))
        ref_max = _parse_decimal(row.get('reference_max'))
        ttype_raw = (row.get('test_type') or '').strip().upper()
        ttype = type_map.get(ttype_raw, LabObservation.ResultTypeEnum.NUMERICAL)
        tg = random.choice(tests)
        test_obj, _ = LabObservation.objects.get_or_create(
            name=row.get('name') or 'Unnamed Test',
            defaults={
                'result_type': ttype,
                'unit_of_measurement': row.get('unit_of_measurement') or None,
                'reference_min': ref_min,
                'reference_max': ref_max,
                'lab_test': tg,
                'created_by': labtech,
            }
        )
        observations.append(test_obj)

    # Seed patients
    patients_df = pd.read_csv('seed_data/mock-patients.csv')
    sex_map = {'MALE': Patient.SexEnum.MALE, 'FEMALE': Patient.SexEnum.FEMALE}
    created_patients = []

    for _, row in patients_df.iterrows():
        dob_raw = row.get('date_of_birth')
        dob = None
        if pd.notna(dob_raw):
            try:
                dob = datetime.strptime(str(dob_raw), '%m/%d/%Y').date()
            except Exception:
                try:
                    dob = datetime.fromisoformat(str(dob_raw)).date()
                except Exception:
                    dob = None

        weight = _parse_decimal(row.get('weight'))
        height = _parse_decimal(row.get('height'))
        sex_val = sex_map.get((row.get('sex') or '').strip().upper())

        patient, _ = Patient.objects.get_or_create(
            first_name=row.get('first_name') or 'First',
            last_name=row.get('last_name') or 'Last',
            date_of_birth=dob or timezone.now().date(),
            defaults={
                'sex': sex_val or Patient.SexEnum.MALE,
                'weight': weight,
                'height': height,
                'region': row.get('region') or Patient.RegionEnum.OTHER,
                'city': row.get('city') or '',
            }
        )
        created_patients.append(patient)

    # Create visits and some lab requests for patients
    now = timezone.now()
    i = 0
    for patient in created_patients:
        # create 0-2 visits per patient
        for _ in range(random.randint(0, 4)):
            # pick a visit time within the past year
            visit_time = now - timedelta(days=random.randint(0, 365), seconds=random.randint(0, 86400))
            print(visit_time)
            i += 1
            visit = Visit.objects.create(
                visit_category=Visit.VisitCategoryEnum.HISTORY_AND_PHYSICAL,
                visit_status=Visit.VisitStatusEnum.AWAITING_PAYMENT,
                patient=patient,
            )
            # ensure DB timestamp is set to our chosen visit_time (bypass auto_now_add)
            Visit.objects.filter(pk=visit.pk).update(created_at=visit_time, updated_at=visit_time)
            # keep the in-memory object in sync so later visit.save() doesn't overwrite our timestamp
            visit.created_at = visit_time
            visit.updated_at = visit_time
            charge = Charge.objects.create(
                visit=visit,
                charge_type=Charge.ChargeTypeEnum.CONSULTATION,
                charge_status=Charge.ChargeStatusEnum.PENDING,
                amount=300,
                charged_by=reception
            )

            Charge.objects.filter(pk=charge.pk).update(created_at=visit_time+timedelta(minutes=1), updated_at=visit_time+timedelta(minutes=1))

            if random.random() < 0.7 and visit.visit_status == Visit.VisitStatusEnum.AWAITING_PAYMENT:
                payment = Payment.objects.create(
                    visit=visit,
                    amount=(charge.amount * Decimal(random.triangular(0.0, 1.0, 1.0))),
                    recorded_by=reception
                )
                Payment.objects.filter(pk=charge.pk).update(created_at=visit_time + timedelta(minutes=2),
                                                           updated_at=visit_time + timedelta(minutes=2))
                visit.transition_to_next_status()
                visit.save()
                # ensure our custom created_at persists (save() may have written the instance value back)
                Visit.objects.filter(pk=visit.pk).update(created_at=visit_time)
                visit.created_at = visit_time

            # optionally create a vital sign record shortly after visit
            if random.random() < 0.7 and visit.visit_status == Visit.VisitStatusEnum.AWAITING_VITALS:
                vs_time = visit_time + timedelta(minutes=random.randint(1, 120))
                if vs_time > now:
                    vs_time = now
                vs = VitalSign.objects.create(
                    visit=visit,
                    recorded_by=random.choice([doctor, labtech, admin]),
                    bp_systolic=random.randint(90, 140),
                    bp_diastolic=random.randint(60, 95),
                    pulse_rate=random.randint(55, 110),
                    respiratory_rate=random.randint(12, 24),
                    temperature=Decimal(str(round(random.uniform(36.0, 38.5), 2))),
                    temperature_unit=VitalSign.TemperatureUnitEnum.CELSIUS,
                    weight=patient.weight or _parse_decimal(random.choice(["70", "65", "80"])) ,
                    weight_unit=VitalSign.WeightUnitEnum.KG,
                    height=patient.height or _parse_decimal(random.choice(["165", "170", "180"])),
                    height_unit=VitalSign.HeightUnitEnum.CENTIMETER,
                )
                VitalSign.objects.filter(pk=vs.pk).update(created_at=vs_time, updated_at=vs_time)
                visit.transition_to_next_status()
                visit.save()
                Visit.objects.filter(pk=visit.pk).update(created_at=visit_time)
                visit.created_at = visit_time

            # optionally create a physical exam
            if random.random() < 0.7 and visit.visit_status == Visit.VisitStatusEnum.AWAITING_CONSULTATION:
                pe_time = visit_time + timedelta(minutes=random.randint(5, 180))
                if pe_time > now:
                    pe_time = now
                pe = PhysicalExam.objects.create(
                    visit=visit,
                    examined_by=doctor,
                    heent='Normal',
                    chest='Clear',
                    cardiovascular='Normal',
                    abdomen='Soft',
                    musculoskeletal='Normal',
                    genitourinary='',
                    cns='Normal',
                    miscellaneous='',
                )
                PhysicalExam.objects.filter(pk=pe.pk).update(created_at=pe_time, updated_at=pe_time)
                visit.transition_to_next_status()
                visit.save()
                Visit.objects.filter(pk=visit.pk).update(created_at=visit_time)
                visit.created_at = visit_time

            # maybe create a lab request for some visits; ensure lab_request time is >= visit_time
            if random.random() < 0.6 and visit.visit_status == Visit.VisitStatusEnum.AWAITING_LAB_PAYMENT:
                lab_time = visit_time + timedelta(hours=random.randint(0, 72), seconds=random.randint(0, 3600))
                if lab_time > now:
                    lab_time = now
                lab_request = LabRequest.objects.create(
                    visit=visit,
                    ordered_by=doctor,
                )
                LabRequest.objects.filter(pk=lab_request.pk).update(created_at=lab_time, updated_at=lab_time)
                # attach 1-4 tests to the lab request with timestamps >= lab_time
                sample_tests = random.sample(tests, k=min(len(tests), random.randint(1, 4)))
                for i, t in enumerate(sample_tests):
                    t_time = lab_time + timedelta(minutes=i)
                    if t_time > now:
                        t_time = now
                    lrt = LabTestRequest.objects.create(
                        lab_test=t,
                        lab_request=lab_request,
                        ordered_by=doctor,
                    )
                    LabTestRequest.objects.filter(pk=lrt.pk).update(created_at=t_time, updated_at=t_time)

                charge = Charge.objects.create(
                    visit=visit,
                    charge_type=Charge.ChargeTypeEnum.LABORATORY,
                    charge_status=Charge.ChargeStatusEnum.PENDING,
                    amount=lab_request.price,
                    charged_by=doctor
                )

                Charge.objects.filter(pk=charge.pk).update(created_at=lab_time + timedelta(minutes=1),
                                                           updated_at=lab_time + timedelta(minutes=1))
                if random.random() < 0.9:
                    payment = Payment.objects.create(
                        visit=visit,
                        amount=(charge.amount * Decimal(random.triangular(0.0, 1.0, 1.0))),
                        recorded_by=reception
                    )
                    Payment.objects.filter(pk=charge.pk).update(created_at=lab_time + timedelta(minutes=2),
                                                                updated_at=lab_time + timedelta(minutes=2))
                    visit.transition_to_next_status()
                    visit.save()
                    Visit.objects.filter(pk=visit.pk).update(created_at=visit_time)
                    visit.created_at = visit_time
                if random.random() < 0.6:
                    visit.transition_to_next_status()
                    visit.save()
                    Visit.objects.filter(pk=visit.pk).update(created_at=visit_time)
                    visit.created_at = visit_time
                if random.random() < 0.6:
                    visit.transition_to_next_status()
                    visit.save()
                    Visit.objects.filter(pk=visit.pk).update(created_at=visit_time)
                    visit.created_at = visit_time
                if random.random() < 0.6:
                    visit.transition_to_next_status()
                    visit.save()
                    Visit.objects.filter(pk=visit.pk).update(created_at=visit_time)
                    visit.created_at = visit_time

    print('Seeding complete:')
    print(f'  Staff: admin, dr_jane, lab_tech')
    print(f'  Tests: {len(tests)}')
