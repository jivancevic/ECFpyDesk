#ifndef FileDataWriter_h
#define FileDataWriter_h

#include "DataWriter.h"
#include <iostream>
#include <fstream>

class FileDataWriter : public DataWriter
{
public:
    FileDataWriter(std::string &fileName);
    ~FileDataWriter();
    void writeData(std::string &data);
    void writeData(char data);
    void writeData(double data);
    void close();
private:
    std::ofstream file;
};

#endif // FileDataWriter_h
