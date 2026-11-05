#ifndef ErrorMetric_h
#define ErrorMetric_h

class ErrorMetric
{
public:
    virtual double calculateError(double y, double t) = 0;
};

#endif // ErrorMetric_h
