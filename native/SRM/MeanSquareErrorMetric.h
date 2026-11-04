#ifndef MeanSquareErrorMetric_h
#define MeanSquareErrorMetric_h

#include "ErrorMetric.h"

class MeanSquareErrorMetric : public ErrorMetric
{
public:
    double calculateError(double y, double t);
};

#endif // MeanSquareErrorMetric_h
