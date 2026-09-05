"""The controlled vocabulary of topics a question may carry.

Used by the eval harness (rule: ``topic`` present and in the allowed
list). Kept as a plain in-code constant - there is no need for config or
a database table at this scope. A ``frozenset`` so callers cannot mutate
the shared vocabulary by accident.
"""

ALLOWED_TOPICS: frozenset[str] = frozenset(
    {
        "arithmetic",
        "fractions",
        "algebra",
        "geometry",
        "measurement",
        "data-and-statistics",
    }
)
