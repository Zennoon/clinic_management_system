from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
import random

import pandas as pd
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from appointments.models import Appointment
from lab_results.models import LabResult, LabObservationResult
from patients.models import Patient
from payments.models import Payment
from staff.models import Staff
from lab_requests.models import LabObservation, LabGroup, LabRequest, LabService
from visits.models import Consultation, Review, Visit
from vital_signs.models import VitalSign
from physical_exams.models import PhysicalExam


def _parse_decimal(value):
    if value is None or pd.isna(value):  # pd.isna catches more variants of null
        return Decimal("0.00")  # Return zero instead of None to prevent math errors
    try:
        s = str(value).strip()
        if s == "" or s.lower() == "nan":
            return Decimal("0.00")
        return Decimal(s)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0.00")


prices = [
    {"price": 140},
    {"price": 320},
    {"price": 1200},
    {"price": 1200},
    {"price": 920},
    {"price": 1460},
    {"price": 520},
    {"price": 820},
    {"price": 1540},
    {"price": 1080},
    {"price": 1540},
    {"price": 1780},
    {"price": 1120},
    {"price": 1340},
    {"price": 220},
    {"price": 1920},
    {"price": 1540},
    {"price": 480},
    {"price": 260},
    {"price": 540},
    {"price": 1480},
    {"price": 400},
    {"price": 180},
    {"price": 1640},
    {"price": 760},
    {"price": 240},
    {"price": 1560},
    {"price": 700},
    {"price": 1740},
    {"price": 1840},
]


@transaction.atomic
def seed_db():
    random.seed(69)
    complaints = "Severe headache, Difficulty breathing, Fever and chills, Abdominal pain, Chest tightness, Dizziness and lightheadedness, Joint pain, Nausea and vomiting, Back pain, Fatigue and weakness".split(
        ", "
    )
    histories = "patient reports feeling tired all the time, patient has a history of migraines, patient experienced chest pain after exercise, patient reports frequent stomach aches, patient has a family history of heart disease".split(
        ", "
    )

    # Create a few staff users used as creators/orderers
    def _ensure_staff(username, role, password="password"):
        user, created = Staff.objects.get_or_create(
            username=username, defaults={"role": role}
        )
        if created:
            user.set_password(password)
            user.save()
        return user

    admin = _ensure_staff("admin", Staff.RoleEnum.ADMIN)
    doctor = _ensure_staff("dr_jane", Staff.RoleEnum.DOCTOR)
    labtech = _ensure_staff("lab_tech", Staff.RoleEnum.LABORATORY)
    reception = _ensure_staff("Sami", Staff.RoleEnum.RECEPTION)

    # Seed test groups
    groups_df = pd.read_csv("seed_data/mock-test-groups.csv")
    groups = []
    for _, row in groups_df.iterrows():
        group, _ = LabGroup.objects.get_or_create(
            name=row.get("name") or "Unnamed",
            defaults={"created_by": admin},
        )
        groups.append(group)

    if not groups:
        # fallback: create one group
        g = LabGroup.objects.create(name="Default", created_by=admin)
        groups.append(g)

    # Seed tests
    observations_df = pd.read_csv("seed_data/mock-tests.csv")
    observations = []
    type_map = {
        "NUMERICAL": LabObservation.ObservationTypeEnum.NUMERICAL,
        "CATEGORICAL": LabObservation.ObservationTypeEnum.CATEGORICAL,
        "NUMERIC": LabObservation.ObservationTypeEnum.NUMERICAL,
    }
    for g in groups:
        obs_list = observations_df.sample(random.randint(1, 3))
        for _, row in obs_list.iterrows():
            test_type = (row.get("type") or "").strip().upper()
            LabObservation.objects.create(
                name=row.get("name") or "Unnamed Test",
                type=type_map.get(
                    test_type, LabObservation.ObservationTypeEnum.NUMERICAL
                ),
                unit_of_measurement=(
                    row.get("unit_of_measurement", None)
                    if type_map.get(
                        test_type, LabObservation.ObservationTypeEnum.NUMERICAL
                    )
                    == LabObservation.ObservationTypeEnum.NUMERICAL
                    else None
                ),
                reference_min=(
                    _parse_decimal(row.get("reference_min"))
                    if type_map.get(
                        test_type, LabObservation.ObservationTypeEnum.NUMERICAL
                    )
                    == LabObservation.ObservationTypeEnum.NUMERICAL
                    else None
                ),
                reference_max=(
                    _parse_decimal(row.get("reference_max"))
                    if type_map.get(
                        test_type, LabObservation.ObservationTypeEnum.NUMERICAL
                    )
                    == LabObservation.ObservationTypeEnum.NUMERICAL
                    else None
                ),
                lab_group=g,
                created_by=labtech,
            )

    lab_services = []
    for g in groups:
        print(f"Group: {g}")
        print(g.lab_observations.all())
        observation_options = list(g.lab_observations.all())
        for j in range(min(random.randint(1, 4), g.lab_observations.count())):

            observations = random.choices(
                observation_options,
                k=int(
                    random.triangular(
                        1, len(observation_options), len(observation_options)
                    )
                ),
            )
            observations = set(observations)
            for obs in observations:
                if obs in observation_options:
                    observation_options.remove(obs)
            starting_index = (len(prices) // 4) * (len(observations) - 1)
            ending_index = min(starting_index + len(prices) // 4, len(prices))
            price = random.choice(prices[starting_index:ending_index])["price"]
            lab_service = LabService.objects.create(
                name=f"Lab Service {j} of {g.name}",
                price=price,
                lab_group=g,
                created_by=admin,
            )

            lab_service.lab_observations.set(observations)
            lab_service.full_clean()
            lab_service.save()
            lab_services.append(lab_service)
            print(lab_service)

    # Seed patients
    patients_df = pd.read_csv("seed_data/mock-patients.csv")
    sex_map = {"MALE": Patient.SexEnum.MALE, "FEMALE": Patient.SexEnum.FEMALE}
    created_patients = []

    for _, row in patients_df.iterrows():
        dob_raw = row.get("date_of_birth")
        dob = None
        if pd.notna(dob_raw):
            try:
                dob = datetime.strptime(str(dob_raw), "%m/%d/%Y").date()
            except Exception:
                try:
                    dob = datetime.fromisoformat(str(dob_raw)).date()
                except Exception:
                    dob = None

        weight = _parse_decimal(row.get("weight"))
        height = _parse_decimal(row.get("height"))
        sex_val = sex_map.get((row.get("sex") or "").strip().upper())

        patient, _ = Patient.objects.get_or_create(
            first_name=row.get("first_name") or "First",
            last_name=row.get("last_name") or "Last",
            date_of_birth=dob or timezone.now().date(),
            defaults={
                "sex": sex_val or Patient.SexEnum.MALE,
                "weight": weight,
                "height": height,
                "region": row.get("region") or Patient.RegionEnum.OTHER,
                "city": row.get("city") or "",
            },
            is_active=(random.random() > 0.1),
        )
        created_patients.append(patient)

    # Create visits and some lab requests for patients
    now = timezone.now()
    i = 0
    for patient in created_patients:
        # create 0-2 visits per patient
        for _ in range(random.randint(0, 4)):
            # pick a visit time within the past year

            visit_time = now - timedelta(
                days=random.randint(0, 60), seconds=random.randint(0, 86400)
            )
            while Visit.objects.filter(
                Q(patient=patient) & Q(date__date=visit_time.date())
            ).exists():
                visit_time = now - timedelta(
                    days=random.randint(0, 60), seconds=random.randint(0, 86400)
                )
            i += 1
            visit = Visit.objects.create(
                visit_category=random.choice(Visit.VisitCategoryEnum.values),
                patient=patient,
                date=visit_time,
                created_by=reception,
                is_active=(random.random() > 0.1),
            )
            consultation_charge = visit.create_consultation_charge(reception)
            if random.random() < 0.1:
                consultation_charge.is_active = False
                consultation_charge.save()
            if not consultation_charge.is_settled:
                rand = random.random()

                if rand < 0.75:
                    payment = visit.pay_charge(
                        charge=consultation_charge,
                        amount=consultation_charge.amount,
                        method=random.choice(
                            [
                                Payment.PaymentMethodEnum.CARD,
                                Payment.PaymentMethodEnum.CASH,
                                Payment.PaymentMethodEnum.MOBILE,
                            ]
                        ),
                        staff=reception,
                    )
                else:
                    waived = random.triangular(0, float(consultation_charge.amount), 0)
                    payment = visit.pay_charge(
                        charge=consultation_charge,
                        amount=float(consultation_charge.amount) - waived,
                        method=random.choice(
                            [
                                Payment.PaymentMethodEnum.CARD,
                                Payment.PaymentMethodEnum.CASH,
                                Payment.PaymentMethodEnum.MOBILE,
                            ]
                        ),
                        staff=reception,
                    )

                    if random.random() < 0.5:
                        visit.pay_charge(
                            charge=consultation_charge,
                            amount=waived,
                            method=Payment.PaymentMethodEnum.WAIVER,
                            staff=reception,
                        )

                randnum = random.random()

                if randnum < 0.25:
                    print("ADJUSTMENT INCOMING...")
                    print(randnum)
                    print(payment.id)
                    payment.create_adjustment(
                        amount=payment.amount * randnum,
                        reason="Seeding purposes",
                        staff=reception,
                    )

            # optionally create a vital sign record shortly after visit
            if (
                random.random() < 0.7
                and visit.visit_status == Visit.VisitStatusEnum.AWAITING_VITALS
            ):
                vs_time = visit_time + timedelta(minutes=random.randint(1, 120))
                if vs_time > now:
                    vs_time = now
                VitalSign.objects.create(
                    visit=visit,
                    recorded_by=random.choice([doctor, labtech, admin]),
                    bp_systolic=random.randint(90, 140),
                    bp_diastolic=random.randint(60, 95),
                    pulse_rate=random.randint(55, 110),
                    respiratory_rate=random.randint(12, 24),
                    temperature=Decimal(str(round(random.uniform(36.0, 38.5), 2))),
                    temperature_unit=VitalSign.TemperatureUnitEnum.CELSIUS,
                    weight=patient.weight
                    or _parse_decimal(random.choice(["70", "65", "80"])),
                    weight_unit=VitalSign.WeightUnitEnum.KG,
                    height=patient.height
                    or _parse_decimal(random.choice(["165", "170", "180"])),
                    height_unit=VitalSign.HeightUnitEnum.CENTIMETER,
                    date=vs_time,
                )
                visit.update_status()

            # optionally create a physical exam
            if (
                random.random() < 0.7
                and visit.visit_status == Visit.VisitStatusEnum.AWAITING_CONSULTATION
            ):
                pe_time = visit_time + timedelta(minutes=random.randint(5, 180))
                if pe_time > now:
                    pe_time = now
                PhysicalExam.objects.create(
                    visit=visit,
                    examined_by=doctor,
                    heent="Normal",
                    chest="Clear",
                    cardiovascular="Normal",
                    abdomen="Soft",
                    musculoskeletal="Normal",
                    genitourinary="",
                    cns="Normal",
                    miscellaneous="",
                    date=pe_time,
                )

                Consultation.objects.create(
                    visit=visit,
                    consulted_by=doctor,
                    chief_complaint=random.choice(complaints),
                    history=random.choice(histories),
                    assessment=random.choice(histories),
                    date=pe_time,
                )

                visit.update_status()

                if random.random() < 0.6:
                    lab_time = visit_time + timedelta(
                        hours=random.randint(0, 2), seconds=random.randint(0, 3600)
                    )
                    if lab_time > now:
                        lab_time = now
                    lab_request = LabRequest.objects.create(
                        visit=visit, ordered_by=doctor, date=lab_time
                    )
                    # attach 1-4 tests to the lab request with timestamps >= lab_time
                    sample_services = random.sample(
                        lab_services, k=min(len(lab_services), random.randint(1, 3))
                    )
                    for i, s in enumerate(sample_services):
                        t_time = lab_time + timedelta(minutes=i)
                        if t_time > now:
                            t_time = now

                        lab_request.lab_services.add(s)
                    lab_request.save()

                    lab_charge = visit.create_lab_request_charge(lab_request, doctor)

                    if random.random() < 0.75:
                        rand = random.random()

                        if rand < 0.75:
                            visit.pay_charge(
                                charge=lab_charge,
                                amount=lab_charge.amount,
                                method=random.choice(
                                    [
                                        Payment.PaymentMethodEnum.CARD,
                                        Payment.PaymentMethodEnum.CASH,
                                        Payment.PaymentMethodEnum.MOBILE,
                                    ]
                                ),
                                staff=reception,
                            )
                        else:
                            waived = random.triangular(0, float(lab_charge.amount), 0)
                            visit.pay_charge(
                                charge=lab_charge,
                                amount=float(lab_charge.amount) - waived,
                                method=random.choice(
                                    [
                                        Payment.PaymentMethodEnum.CARD,
                                        Payment.PaymentMethodEnum.CASH,
                                        Payment.PaymentMethodEnum.MOBILE,
                                    ]
                                ),
                                staff=reception,
                            )

                            if random.random() < 0.5:
                                visit.pay_charge(
                                    charge=lab_charge,
                                    amount=waived,
                                    method=Payment.PaymentMethodEnum.WAIVER,
                                    staff=reception,
                                )

            if (
                random.random() <= 0.8
                and visit.visit_status is Visit.VisitStatusEnum.AWAITING_LAB_RESULT
            ):
                lab_requests = visit.lab_requests
                for request in lab_requests.all():
                    lab_result = LabResult.objects.create(
                        lab_request=request, reported_by=labtech
                    )
                    for obs in request.observations:
                        obs_result = LabObservationResult.objects.create(
                            value_numeric=(
                                random.randint(1, 100)
                                if obs.type
                                is LabObservation.ObservationTypeEnum.NUMERICAL
                                else None
                            ),
                            value_categorical=(
                                random.choice(
                                    LabObservationResult.CategoricalEnum.values
                                )
                                if obs.type
                                is LabObservation.ObservationTypeEnum.CATEGORICAL
                                else None
                            ),
                            date=lab_time,
                            lab_observation=obs,
                            lab_result=lab_result,
                            reported_by=labtech,
                        )
                visit.update_status()

            if (
                random.random() <= 0.7
                and visit.visit_status is Visit.VisitStatusEnum.AWAITING_REVIEW
            ):
                review = Review.objects.create(visit=visit, reviewed_by=doctor)
                visit.update_status()

            if (
                random.random() < 0.25
            ) and visit.visit_status == Visit.VisitStatusEnum.COMPLETED:
                Appointment.objects.create(
                    date=visit_time,
                    appointment_date=visit_time + timedelta(days=random.randint(7, 90)),
                    patient=patient,
                    doctor=doctor,
                    visit=visit,
                )
            print(visit.visit_status)

    print("Seeding complete:")
    print(f"  Staff: admin, dr_jane, lab_tech")
    print(f"Lab groups: {groups}")
    print(f"Lab groups: {observations}")
    print(f"Lab groups: {lab_services}")
