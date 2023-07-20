import math
from scipy.stats import norm

def calculate_option_price(stock_price, strike_price, time_to_expiration, risk_free_rate, volatility):
    d1 = (math.log(stock_price / strike_price) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiration) / (volatility * math.sqrt(time_to_expiration))
    d2 = d1 - volatility * math.sqrt(time_to_expiration)

    call_price = stock_price * norm.cdf(d1) - strike_price * math.exp(-risk_free_rate * time_to_expiration) * norm.cdf(d2)
    put_price = strike_price * math.exp(-risk_free_rate * time_to_expiration) * norm.cdf(-d2) - stock_price * norm.cdf(-d1)

    return call_price, put_price

def calculate_greeks(stock_price, strike_price, time_to_expiration, risk_free_rate, volatility):
    d1 = (math.log(stock_price / strike_price) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiration) / (volatility * math.sqrt(time_to_expiration))
    d2 = d1 - volatility * math.sqrt(time_to_expiration)

    delta_call = norm.cdf(d1)
    delta_put = norm.cdf(d1) - 1
    gamma = norm.pdf(d1) / (stock_price * volatility * math.sqrt(time_to_expiration))
    vega = stock_price * norm.pdf(d1) * math.sqrt(time_to_expiration)
    theta_call = (-stock_price * norm.pdf(d1) * volatility) / (2 * math.sqrt(time_to_expiration)) - risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiration) * norm.cdf(d2)
    theta_put = (-stock_price * norm.pdf(d1) * volatility) / (2 * math.sqrt(time_to_expiration)) + risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiration) * norm.cdf(-d2)
    rho_call = strike_price * time_to_expiration * math.exp(-risk_free_rate * time_to_expiration) * norm.cdf(d2)
    rho_put = -strike_price * time_to_expiration * math.exp(-risk_free_rate * time_to_expiration) * norm.cdf(-d2)

    return delta_call, delta_put, gamma, vega, theta_call, theta_put, rho_call, rho_put

# Example usage
stock_price = 100
strike_price = 105
time_to_expiration = 0.5
risk_free_rate = 0.05
volatility = 0.2

call_price, put_price = calculate_option_price(stock_price, strike_price, time_to_expiration, risk_free_rate, volatility)
delta_call, delta_put, gamma, vega, theta_call, theta_put, rho_call, rho_put = calculate_greeks(stock_price, strike_price, time_to_expiration, risk_free_rate, volatility)

print("Call Price:", call_price)
print("Put Price:", put_price)
print("Delta (Call):", delta_call)
print("Delta (Put):", delta_put)
print("Gamma:", gamma)
print("Vega:", vega)
print("Theta (Call):", theta_call)
print("Theta (Put):", theta_put)
print("Rho (Call):", rho_call)
print("Rho (Put):", rho_put)
