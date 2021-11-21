"""
SUMMARY

Continuous variables.
"""


from .common import Common

import numpy as np
from scipy.stats import beta
from scipy.stats import norm
from scipy.stats import uniform


integral_resolution = 20 # intervals
integral_points = 1 + integral_resolution



# Creates a number of continuous distributions ranges
def generate_discretized_continuous_distribution(given_variable_name, distribution_name, separating_points, distribution_parameter_values):

    # Sorts the separating points so that these can be processed in order
    ordered_separating_points = sorted(separating_points)

    # enforces known distribution
    assert distribution_name in ["uniform", "normal", "beta", "pareto"], "'%s' distribution is not accepted" % (distribution_name, )

    # Enforces all parameters to be numeric
    for a_param in distribution_parameter_values:
        param_type = type(a_param).__name__
        assert (param_type == "int") or (param_type == float), "All parameters, must be int or float type, not '%s'" % (param_type, )


    # Generates the different distributions
    if distribution_name == "uniform":

        a, b = distribution_parameter_values
        enforce_array_within_lu(ordered_separating_points, a, b)

        # Adds the points to the range as the start and end
        ordered_separating_points = [a] + ordered_separating_points + [b]

        created_distributions = []

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(uniform_distribution(given_variable_name, l, u, a, b))

    elif distribution_name == "normal":
        μ, σ = distribution_parameter_values

        five_sigma = 5*σ

        # If no interval ranges, utilize 5σ (> 99.9999 of the distribution)
        if ordered_separating_points == []:
            ordered_separating_points = [μ - five_sigma, μ + five_sigma]
        # If there is one or more values, get the ends at 5σ in one distance and 5σ from the peak in the other distance if peak not within values
        else:
            furthest_left  = ordered_separating_points[0]
            furthest_right = ordered_separating_points[-1]

            # Do 5σ in both distances if the peak (μ) is contained within the interval
            if check_within_interval(μ, furthest_left, furthest_right, contains=False):
                ordered_separating_points = [furthest_left - five_sigma] + ordered_separating_points + [furthest_right + five_sigma]

            # Not contained
            # If left of the furthest left, go 5σ left of the peak
            elif μ < (furthest_left - five_sigma):
                ordered_separating_points = [μ - five_sigma] + ordered_separating_points + [furthest_right + five_sigma]
            # if right of the furthest right, go 5σ right of the peak
            else:
                ordered_separating_points = [furthest_left - five_sigma] + ordered_separating_points + [μ + five_sigma]

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(normal_distribution(given_variable_name, l, u, μ, σ))


    # Generates the different distributions
    elif distribution_name == "beta":

        α, β = distribution_parameter_values
        enforce_array_within_lu(ordered_separating_points, 0, 1)

        # Adds the points to the range as the start and end
        ordered_separating_points = [a] + ordered_separating_points + [b]

        created_distributions = []

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(uniform_distribution(given_variable_name, l, u, α, β))


    # Generates the different distributions
    elif distribution_name == "pareto":

        x_m. α = distribution_parameter_values
        enforce_array_within_lu(ordered_separating_points, x_m, np.inf)

        # End point asssigned as the place where CDF >= 0.999999 (close to the 5*σ for the normal distribution)
        if ordered_separating_points == []:
            end_point = x_m/(0.000001**(1/α))
        else:
            end_point = ordered_separating_points[-1] + x_m/(0.000001**(1/α))

        ordered_separating_points = [x_m] + ordered_separating_points + [end_point]

        created_distributions = []

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(uniform_distribution(given_variable_name, l, u, x_m. α))

    return created_distributions



# Common continuous function
# Designed as an abstract class to automatically describe the variable in an unified format
def common_continuous(Common):

    def __init__(self, given_variable_name, distribution_name, distribution_parameter_names, distribution_parameter_values,
        given_expectation, given_variance, lower_bound, upper_bound, probability):

        # Enforces the same number of parameters names and values
        assert len(distribution_parameter_names) == len(distribution_parameter_names), "Different number of parameter names and values"

        # Joins the parameter names and values with an "=" values
        # Greek alphabet obtained from https://en.wikipedia.org/wiki/Greek_alphabet
        # e.g.: μ=10.000
        parameters_together = []

        for a_pn, a_pv in zip(distribution_parameter_names, distribution_parameter_values):
            parameters_together.append("%s=%.4f" % (a_pn, a_pv))


        formatted_variable_class = distribution_name + "(" + ", ".join(parameters_together) + ")"

        Common.__init__(self, given_variable_name, formatted_variable_class, given_expectation, given_variance, lower_bound, upper_bound, probability)



# Uniform distributions
def uniform_distribution(common_continuous):

    # a (int/float): Start of range
    # b (int/float): End of range
    def __init__(self, given_variable_name, lower_bound, upper_bound, a, b):

        # Enforces a <= b
        assert a <= b, "a=%.4f > b=%.4f" % (a, b)

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.uniform.html
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(lower_bound, upper_bound), cdist=uniform(loc = a, scale = b))

        common_continuous.__init__(self, given_variable_name, "Uniform", distribution_parameter_names, distribution_parameter_values,
            E, Var, lower_bound, upper_bound, probability)



# Normal (Gaussian) distributions
def normal_distribution(common_continuous):

    # μ (int/float): Expectationn
    # σ (int/float): Standard deviation
    def __init__(self, given_variable_name, lower_bound, upper_bound, μ, σ):

        # Standardizes variables
        zl = z_standardizer(lower_bound, μ, σ)
        zu = z_standardizer(upper_bound, μ, σ)

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(zl, zu), cdist=norm())

        common_continuous.__init__(self, given_variable_name, "Normal", distribution_parameter_names, distribution_parameter_values,
            E, Var, lower_bound, upper_bound, probability)



# Beta distributions
def beta_distribution(common_continuous):

    # α (int/float)
    # β (int/float)
    def __init__(self, given_variable_name, lower_bound, upper_bound, α, β):

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.beta.html
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(lower_bound, upper_bound), cdist=beta(α, β))

        common_continuous.__init__(self, given_variable_name, "Beta", distribution_parameter_names, distribution_parameter_values,
            E, Var, lower_bound, upper_bound, probability)



# Pareto distributions
def pareto_distribution(common_continuous):

    # α (int/float)
    # β (int/float)
    def __init__(self, given_variable_name, lower_bound, upper_bound, x_m. α):

        # Enforces real values
        # Based on https://en.wikipedia.org/wiki/Pareto_distribution
        assert x_m > 0, "x_m cannot be zero or below"
        assert α > 0, "α cannot be zero or below"

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pareto.html
        # https://en.wikipedia.org/wiki/Pareto_distribution
        # https://towardsdatascience.com/generating-pareto-distribution-in-python-2c2f77f70dbf
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(lower_bound, upper_bound), cdist=pareto(α, scale=x_m))

        common_continuous.__init__(self, given_variable_name, "Beta", distribution_parameter_names, distribution_parameter_values,
            E, Var, lower_bound, upper_bound, probability)



# calculates the z standardization
# z = (x - μ)/σ
def z_standardizer(x, μ, σ):
    return (x - μ)/σ



# Gets a set of equally spaced integral points
# Designed for calculating expectations and variances
def get_integral_points(l, u):
    return np.linspace(l, u, integral_points)



# Gets the points inbetween points of an array
def get_inbetween(given_array):
    A = []

    for nv in range(0, (len(given_array) - 1)):
        A.append(0.5*(given_array[nv] + given_array[nv + 1]))

    return A



# Calculates the probability, expectation, and variance
# ab (arr) (int/float): a, b points
# cdist (scipy.stats.X): Must only take a single value for its "pdf" and "cfd" methods
def get_PR_E_Var(ab, cdist):

    probability = cdist.cdf(ab[-1]) - cdist.cdf(ab[0])

    ab_2 = get_inbetween(ab)

    # Calculates the expectation and variance within the interval
    E   = 0
    Var = 0

    # "integral_resolution" variable could be used instead, but implemented as below for clarity
    for ma in range(0, (integral_points - 1)):
        a = ab[ma]
        b = ab[ma + 1]
        ab_2 = 0.5*(a + b)

        E_f_a = a*cdist.pdf(a)
        E_f_b = b*cdist.pdf(b)
        E_f_ab_2 = ab_2*cdist.pdf(ab_2)

        V_f_a = (a**2)*cdist.pdf(a)
        V_f_b = (b**2)*cdist.pdf(b)
        V_f_ab_2 = (ab_2**2)*cdist.pdf(ab_2)


        # Integral always determined with Simpson's rule (1/3)
        E   += ((b - a)/6)*(E_f_a + 4*E_f_ab_2 + E_f_b)
        Var += ((b - a)/6)*(V_f_a + 4*V_f_ab_2 + V_f_b) - E**2


    # Divides the result by the probability to make it accurate
    E   /= probability
    Var /= probability

    return [probability, E, Var]



# Checks (but not enforces) if a variable is contained within an interval
def check_within_interval(x, l, u, contains):
    if contains:
        return (l <= x) and (x <= u)
    else:
        return (l < x) and (x < u)



# Enforces that a value is within a lower and upper bound
# l <= u, not checked
def enforce_x_within_lu(x, l, u):

    assert(l <= x), "%.4f < %.4f" % (x, l)
    assert(x <= u), "%.4f > %.4f" % (x, u)



# Enforces that all the values in an array are within lower and upper bounds
# l <= u, checked
def enforce_array_within_lu(given_array, l, u):

    # Enforces that lower bound is below upper bound
    assert l <= u, "%.4f > %.4f" % (l, u)

    for x in given_array:
        enforce_x_within_lu(x, l, u)
