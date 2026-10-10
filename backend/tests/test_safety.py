from src.safety_engine import check_safety


tests = [
    "I have difficulty breathing",
    "I have a high fever",
    "I have a mild headache",
]


for description in tests:
    result = check_safety(description)

    print("\nInput:", description)
    print("Urgency:", result["urgency"])
    print("Signals:", result["matched_signals"])
    print("Action:", result["action"])