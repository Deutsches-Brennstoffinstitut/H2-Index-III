def price_dyn_factor_b(interest_rate: float, price_dev_factor: float, time_period_of_annuity: int):
    """
    Function to determine the price_dynamic_factor_b of VDI 2067
    Args:
        interest_rate: Interest rate of the component as 1 + ((interest_rate in percent) / 100)
        price_dev_factor: Price dev factor of the component as 1 + ((price_dev_factor in percent) / 100)
        time_period_of_annuity: Time period of the annuity in years

    """
    if price_dev_factor == interest_rate:
        price_dyn_factor_b = time_period_of_annuity / interest_rate
    else:
        price_dyn_factor_b = (1 - (price_dev_factor / interest_rate) ** time_period_of_annuity) / \
                           (interest_rate - price_dev_factor)
    return price_dyn_factor_b


def annuity_factor(interest_rate: float, time_period_of_annuity: int):
    """

    Args:
        interest_rate:  Interest rate of the component as 1 + ((interest_rate in percent) / 100)
        time_period_of_annuity: Time period of the annuity in years
    """

    return (interest_rate - 1) / (1 - interest_rate ** (-time_period_of_annuity))
