
#include <stdint.h>
#include <pybind11/pybind11.h>

namespace py = pybind11;

class Stream
{
public:
	Stream(char* ptr, int size);
	~Stream();
	
};


enum class State : uint32_t {
	// 初始状态
	kStart,
	// kStart meet #
	kMacro,
	// meet a char
	kStartChar,



};


class Parser
{
	State state_ = State::kStart;
public:
	Parser();
	~Parser();
	
	int Parse(Stream& s) {
		return 0;
	};

	// 处理file的时候，初始状态的是 kStart
	int ParseFile(Stream& s) {

	}
};