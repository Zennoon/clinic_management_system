from bs4 import BeautifulSoup
import sys
import copy

with open("scroll-icon.html", "r", encoding="utf-8") as icon_file:
    icon_soup = BeautifulSoup(icon_file, "html.parser")
    icon_copy = copy.copy(icon_soup)


def modify_table_cells(filename):
    print("=" * 200)
    print(filename)
    with open(filename, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    for tr in soup.find_all("tr"):
        print(tr)
        for index, cell in enumerate(tr.find_all(["td", "th"], recursive=False)):
            if index == 0:
                if cell.name != "th":
                    new_tag = soup.new_tag("th", attrs=cell.attrs)
                    new_tag.extend(cell.contents)
                    cell.replace_with(new_tag)
            else:
                if cell.name != "td":
                    new_tag = soup.new_tag("td", attrs=cell.attrs)
                    new_tag.extend(cell.contents)
                    cell.replace_with(new_tag)
        print("*" * 100)
        print(tr)
        break

    with open(filename, "w", encoding="utf-8") as file:
        file.write(str(soup))


def pin_table_cols(filename):
    with open(filename, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    for table in soup.find_all("table"):
        table["class"].remove("table_pinned_rows")
        table["class"].append("table-pin-cols")

    with open(filename, "w", encoding="utf-8") as file:
        file.write(str(soup))


def add_scroll_indicator(filename):
    with open(filename, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    for table in soup.find_all("table"):
        print("#" * 200)
        table_wrapper = table.parent
        print(table_wrapper)

        container = soup.new_tag("div", attrs={"class": "flex flex-col gap-2"})

        new_container = table_wrapper.wrap(container)
        new_container.insert(0, icon_copy)

        print(new_container)

    with open(filename, "w", encoding="utf-8") as file:
        file.write(str(soup))


def remove_script_elements(filename):
    with open(filename, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    for script in soup.find_all("script"):
        print(script)
        script.extract()
    with open(filename, "w", encoding="utf-8") as file:
        file.write(str(soup))


def add_table_wrapper_class_and_data_attr(filename):
    with open(filename, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    for span in soup.find_all("span", class_="scroll-indicator"):
        parent = span.parent
        if not parent.has_attr("data-scroll-sync"):
            parent["data-scroll-sync"] = None

        table = parent.find("table")
        if table and table.has_attr("class") and "table-wrapper" in table["class"]:
            table["class"].remove("table-wrapper")
        table_wrapper = table.parent
        if table_wrapper:
            if not table_wrapper.has_attr("class") or "table-wrapper" not in table_wrapper["class"]:
                table_wrapper["class"] = table_wrapper.get("class", []) + ["table-wrapper"]

    with open(filename, "w", encoding="utf-8") as file:
        file.write(str(soup))


# This block ensures the function runs when the script is executed directly.
if __name__ == "__main__":
    if len(sys.argv) > 2:
        command = sys.argv[1]
        if command == "replace_th_td":
            modify_table_cells(sys.argv[-1])
        elif command == "pin_table_cols":
            pin_table_cols(sys.argv[-1])
        elif command == "add_scroll_indicator":
            add_scroll_indicator(sys.argv[-1])
        elif command == "remove_script_elements":
            remove_script_elements(sys.argv[-1])
        elif command == "add_table_wrapper_class_and_data_attr":
            add_table_wrapper_class_and_data_attr(sys.argv[-1])

    else:
        print("Error: No filename and/or command provided.")
