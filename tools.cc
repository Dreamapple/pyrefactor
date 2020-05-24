
#include <pybind11/pybind11.h>

namespace py = pybind11;

class Stream
{
public:
	Stream(char* ptr, int size);
	~Stream();
	
};