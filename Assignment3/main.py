
import re

def normalise_phone(phone):
    digits = re.sub(r"\D", "", phone)

    # Remove Indian country code when present
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]

    return digits


def normalise_email(email):
    return email.strip().lower()


def normalise_name(name):
    return " ".join(name.strip().lower().split())


def merge_contacts(records):
    merged = {}

    for record in records:
        name = record.get("name", "")

        phones = {
            normalise_phone(p)
            for p in record.get("phones", [])
            if normalise_phone(p)
        }

        emails = {
            normalise_email(e)
            for e in record.get("emails", [])
            if normalise_email(e)
        }

        # Select a phone number as the main key
        if phones:
            key = sorted(phones)[0]
        else:
            key = "NO_PHONE:" + normalise_name(name)

        # Create contact if it does not exist
        if key not in merged:
            merged[key] = {
                "names": set(),
                "phones": set(),
                "emails": set()
            }

        # Add contact information
        if name:
            merged[key]["names"].add(name)

        merged[key]["phones"].update(phones)
        merged[key]["emails"].update(emails)

    return merged


contacts = [
    {
        "name": "Dr. Ravi",
        "phones": ["+91 98400 12345"],
        "emails": ["RAVI@example.com"]
    },
    {
        "name": "ravi kumar",
        "phones": ["9840012345", "044-22223333"],
        "emails": ["ravi@example.com", "rk@example.com"]
    },
    {
        "name": "Meena",
        "phones": ["+91 90000 11111"],
        "emails": ["meena@example.com"]
    },
    {
        "name": "MEENA",
        "phones": ["9000011111"],
        "emails": ["MEENA@example.com"]
    },
    {
        "name": "No Phone Contact",
        "phones": [],
        "emails": ["onlymail@example.com"]
    }
]

result = merge_contacts(contacts)

for key, details in result.items():
    print("Key:", key)
    print("Names:", sorted(details["names"]))
    print("Phones:", sorted(details["phones"]))
    print("Emails:", sorted(details["emails"]))
    print()
