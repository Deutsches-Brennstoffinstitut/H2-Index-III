
def solver_newton(target:float=0, func=None, args:tuple=None, x0:float=1, x_min:float=-1e99, x_max:float=1e99, dx=None, eps_abs:float=0.1, eps_rel:float=0.01, n_min:int=1, n_max:int=100):
    """
    numeric solver using the newton algorithm
    :params target:     specify the solver target scalar number, 1e99=maximum, 1e-99=minimum...
    :params func:       the solving function(x, args)
    :params x0:         starting point
    :params x_min:      minimum allowed input value, default=-1e99
    :params x_max:      maximum allowed input value, default=1e99
    :params dx:         specify the secant stepsize for gradient calculation, default=eps_abs/100
    :params eps_abs:    absolute deviation stop criteria, default=0.1
    :params eps_rel:    relative deviation stop criteria, default=0.04
    :params n_min:      minimum run count, default=1
    :params n_max:      maximum run count, default=100
    :return:            solved x-value where the target condition is met
    """

    modus = -1 if target <= 1e-99 else 1 if target >= 1e99 else 0  # Standart: Löse nach Ziel, z.B. ZERO
    run = True
    x_akt = x0
    dx = dx if dx is not None else eps_abs/100                     # Schrittweite zur Berechnung des gradients
    n = 0

    # run solver
    while run:
        n += 1
        # check if actual value hits boundaries, for upper boundary gradient calcuation must be switched
        if x_akt+dx > x_max:
            x_akt = x_max
            y0 = func(x_akt, args)
            y1 = func(x_akt - dx, args)
            gradient = (y0 - y1) / dx if dx != 0 else 0  # calc gradient
        else:
            if x_akt < x_min:                           # limit to lower boundary
                x_akt = x_min
            y0 = func(x_akt, args)
            y1 = func(x_akt + dx, args)
            gradient = (y1 - y0) / dx if dx != 0 else 0 # calc gradient

        if modus == 0:                            	    # run zero/target solver
            step = (target - y0) / gradient if gradient != 0 else 0
            x_akt += step

            run  = gradient != 0
            run &= abs(y0-target) > eps_abs
            run &= abs(y0-target)/target > eps_rel
            run &= n < n_max
            run |= n < n_min

        elif (modus == -1) | (modus == 1):             # Minimum / Maximum solver
            step = -gradient if modus == -1 else gradient
            x_akt += step
            run  = abs(gradient) > eps_abs
            run &= abs(gradient)/y0 > eps_rel
            run &= n < n_max
            run |= n < n_min

        else:
            run = False

    return x_akt
