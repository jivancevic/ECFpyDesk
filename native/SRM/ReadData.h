#include<vector>

//
// reads delimited data from file; returns data as vector of vectors
//
template <class T>
bool readDataFromFile(std::vector< vector<T> >& data, string fileName)
{
	ifstream file(fileName.c_str());
	if(!file)
		return false;

	data.clear();
	string line;
	uint instance = 0;

	while(getline(file, line)) {
		vector<T> set;
		data.push_back(set);
		stringstream ss(line);
		T datum;
		while(ss >> datum)
			data[instance].push_back(datum);
		instance++;
	}

	return true;
}
