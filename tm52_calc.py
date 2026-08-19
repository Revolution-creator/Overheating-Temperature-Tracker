"""
The actual TM52 maths, kept separate from data-fetching so it's easy to
test on its own with known numbers.
"""


def next_running_mean_temp(previous_trm: float, yesterday_mean_temp: float, alpha: float) -> float:
    """
    Recursive daily update of the running mean outdoor temperature (Trm).

    Trm(today) = (1 - alpha) * Tod-1  +  alpha * Trm(yesterday)

    previous_trm: yesterday's Trm value (float)
    yesterday_mean_temp: yesterday's mean daily external air temp, Tod-1 (float)
    alpha: smoothing constant (0.8 per TM52/EN16798)
    """
    return (1 - alpha) * yesterday_mean_temp + alpha * previous_trm


def seed_running_mean_temp(previous_seven_days_mean_temps: list[float], alpha: float) -> float:
    """
    Full 7-term expansion, used ONCE to establish a starting Trm when you
    have no prior Trm value yet.

    Trm = (1 - alpha) * (Tod-1 + alpha*Tod-2 + alpha^2*Tod-3 + ... + alpha^6*Tod-7)

    previous_seven_days_mean_temps: list of 7 daily mean temps, MOST RECENT FIRST
                                     i.e. [Tod-1, Tod-2, ..., Tod-7]
    """
    if len(previous_seven_days_mean_temps) != 7:
        raise ValueError("Need exactly 7 days of prior mean temperatures to seed Trm")

    weighted_sum = sum(
        (alpha ** i) * temp for i, temp in enumerate(previous_seven_days_mean_temps)
    )
    return (1 - alpha) * weighted_sum


def upper_threshold_temp(trm: float, delta_t: float) -> float:
    """
    TM52 / EN16798 adaptive upper comfort limit.

    Tmax = 0.33 * Trm + 18.8 + delta_t
    """
    return 0.33 * trm + 18.8 + delta_t
