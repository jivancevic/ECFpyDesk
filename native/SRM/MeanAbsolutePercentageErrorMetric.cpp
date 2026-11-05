#include "MeanAbsolutePercentageErrorMetric.h"

#include <math.h>

double MeanAbsolutePercentageErrorMetric::calculateError(double y, double t)
{
    return fabs((t - y) / t);
}



