#include "MeanAbsoluteErrorMetric.h"

#include <math.h>

double MeanAbsoluteErrorMetric::calculateError(double y, double t)
{
    return fabs(y - t);
}



