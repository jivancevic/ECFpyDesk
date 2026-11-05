#ifndef MeanAbsoluteErrorMetric_h
#define MeanAbsoluteErrorMetric_h

#include "ErrorMetric.h"

class MeanAbsoluteErrorMetric : public ErrorMetric
{
public:
    double calculateError(double y, double t);
};

#endif // MeanAbsoluteErrorMetric_h
