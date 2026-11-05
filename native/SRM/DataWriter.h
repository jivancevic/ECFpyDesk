#ifndef DataWriter_h
#define DataWriter_h

#include <iostream>

class DataWriter
{
public:
    virtual void writeData(std::string &data) {}
    virtual void writeData(char data) {}
    virtual void writeData(double data) {}
    virtual void close() {}
};

#endif // DataWriter_h
