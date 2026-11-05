#include "FileDataWriter.h"
#include <string>


FileDataWriter::FileDataWriter(std::string &fileName)
{
	file.open(fileName.c_str());
}


FileDataWriter::~FileDataWriter()
{
    close();
}


void FileDataWriter::writeData(std::string &data)
{
   file << data;
}


void FileDataWriter::writeData(char data)
{
    file << data;
}


void FileDataWriter::writeData(double data)
{
    file << data;
}


void FileDataWriter::close()
{
    file.close();
}
