"""
Module 4: PII Protection
Masks Personally Identifiable Information (PII) in-place using deterministic rule-based patterns.
NO external libraries required — pure Python string operations.

Masking Strategy
----------------
Email  : Show first 2 chars, mask the rest up to @, keep domain.
         john.doe@gmail.com  →  jo****@gmail.com
Phone  : Show last 4 digits, mask the rest with *.
         9876543210          →  ******3210
Name   : We retain customer name for business analytics (city/category aggregations need it
         for de-duplication). A note in the data dictionary flags it as PII. In a production
         system it would be tokenised via a secure vault; here we apply a partial mask:
         "John Smith" → "J*** S****"

Interview talking point: Always apply the principle of minimal exposure —
mask at the earliest possible stage in the pipeline (right after cleaning, before enrichment).
"""

import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def mask_email(email: str) -> str:
    """jo****@gmail.com"""
    if not isinstance(email, str) or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"{local}****@{domain}"
    return f"{local[:2]}{'*' * (len(local) - 2)}@{domain}"


def mask_phone(phone) -> str:
    """******3210  (last 4 digits visible)"""
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) < 4:
        return "****"
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


def mask_name(name: str) -> str:
    """J*** S****"""
    if not isinstance(name, str):
        return name
    parts = name.strip().split()
    masked_parts = []
    for part in parts:
        if len(part) == 0:
            continue
        masked_parts.append(part[0] + "*" * (len(part) - 1))
    return " ".join(masked_parts)


def apply_pii_masking(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all PII masks to a retail transactions DataFrame.
    Operates on copies of columns — original PII values are not retained.
    """
    df = df.copy()

    if "email" in df.columns:
        df["email"] = df["email"].apply(mask_email)
        logger.info("  Email column masked")

    if "phone" in df.columns:
        df["phone"] = df["phone"].apply(mask_phone)
        logger.info("  Phone column masked")

    if "customer_name" in df.columns:
        df["customer_name"] = df["customer_name"].apply(mask_name)
        logger.info("  Customer name column masked")

    logger.info("✅ PII masking applied")
    return df


if __name__ == "__main__":
    sample = pd.DataFrame({
        "customer_name": ["John Smith", "Maria Robinson", "A B"],
        "email": ["john@gmail.com", "MariaRobinson@gmail.com", "x@y.com"],
        "phone": ["9876543210", "8794772717", "123"],
    })
    print(apply_pii_masking(sample))
