"""Placeholder for source adapters.

Do not publish anything from here yet. X/Instagram source retrieval must be
implemented and tested before automatic posting is enabled.
"""

SOURCES = [
    {"platform": "x", "handle": "animetherapy"},
    {"platform": "x", "handle": "ahmedm94m"},
    {"platform": "x", "handle": "ascom0"},
    {"platform": "x", "handle": "animerakuar"},
    {"platform": "instagram", "handle": "k_uroi"},
]


def main():
    print("ANIVO source check placeholder.")
    print(f"{len(SOURCES)} planned sources are configured, but none are active.")
    for source in SOURCES:
        print(f"- {source['platform']}: @{source['handle']}")
    print("No posts were fetched or sent.")

if __name__ == "__main__":
    main()
