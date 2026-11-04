#include "MeanSquareErrorMetric.h"

double MeanSquareErrorMetric::calculateError(double y, double t)
{
    double diff = y - t;
    return diff * diff;
}



