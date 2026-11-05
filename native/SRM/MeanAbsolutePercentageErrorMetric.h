#ifndef MeanAbsolutePercentageErrorMetric_h
#define MeanAbsolutePercentageErrorMetric_h

#include "ErrorMetric.h"

class MeanAbsolutePercentageErrorMetric : public ErrorMetric
{
public:
    double calculateError(double y, double t);
};

#endif // MeanAbsolutePercentageErrorMetric_h
