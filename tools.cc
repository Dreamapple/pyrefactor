
// cl tools.cc -ID:\Miniconda3\Include -ID:\Miniconda3\Library\include D:\Miniconda3\libs\python37.lib /LD /link /out:tools.pyd
#include <stdint.h>
#include <string.h>
#include <map>
#include <pybind11/pybind11.h>

namespace py = pybind11;

std::unordered_set<int> all_c = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '_'};

class Stream
{
public:
	Stream(char* ptr, int size);
	~Stream();
	
};


enum class State : uint32_t {
	// init state
	kStart,
	// kStart meet #
	kMacro,
	// meet a char
	kStartChar,



};


std::map<std::pair<State, int>, State> transMap = {
	{{State::kStart, '#'}, State::kMacro},
	{{State::kStart, '#'}, State::kMacro},
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

};

bool match(char* ptr, char* subtoken) {
	while (true) {
		if (*subtoken == '\0') {
			return true;
		}
		if (*ptr++ != *subtoken++) {
			return false;
		}
	}
	return false;
}

int find(char* ptr, char* subtoken, int debug_level) {
	char* ori = ptr;
	int p_stack = 0;
	char stack[128];
	memset(stack, 0, 128);

	char* ppos;
	bool meet;

	if (*subtoken == '\0') {
		return ptr-ori;
	}
	while (*ptr != '\0') {
		if (debug_level > 10) printf("[#] view %c, p_stack=%d\n", *ptr, p_stack);
		if (p_stack == 0 && match(ptr, subtoken)) {
			return ptr-ori;
		}
		switch (*ptr) {
		case '(':
		case '{':
		case '[':
			stack[p_stack++] = *ptr++;
			break;
		case ')':
			if (p_stack <= 0) {
				return -2000;
			}
			if (stack[--p_stack] != '(' ) {
				printf("stack not balance\n");
				printf("%s\n", ptr);
				return -1000;
			}
			ptr++;
			break;
		case '}':
			if (p_stack <= 0) {
				return -2001;
			}
			if (stack[--p_stack] != '{' ) {
				printf("stack not balance\n");
				printf("%s\n", ptr);
				return -1001;
			}
			ptr++;
			break;
		case ']':
			if (p_stack <= 0) {
				return -2002;
			}
			if (stack[--p_stack] != '[' ) {
				printf("stack not balance\n");
				printf("%s\n", ptr);
				return -1002;
			}
			ptr++;
			break;
		case '\"':
			ptr++;
			meet = false;
			while (!meet && *ptr != '\0') {
				switch (*ptr) {
				case '\"':
					meet = true;
					ptr += 1;
					break;
				case '\\':
					ptr += 2;
					break;
				default:
					ptr += 1;
				}
			}
			break;
		case '\'':
			ptr++;
			meet = false;
			while (!meet && *ptr != '\0') {
				switch (*ptr) {
				case '\'':
					meet = true;
					ptr += 1;
					break;
				case '\\':
					ptr += 2;
					break;
				default:
					ptr += 1;
				}
			}
			break;
		case '/':
			ptr += 1;
			meet = false;
			if (*ptr == '/') {
				ptr += 1;
				while (!meet && *ptr != '\0') {
					if (*ptr == '\n') {
						meet = true;
						ptr += 1;
						break;
					} else {
						ptr += 1;
					}
				}
			} else if (*ptr == '*') {
				ptr += 1;
				while (!meet && *ptr != '\0') {
					if (*ptr == '*' && *(ptr+1) == '/') {
						meet = true;
						ptr += 2;
						break;
					} else {
						ptr += 1;
					}
				}
			}
			break;
		case '#':
			while (*ptr != '\0' && *ptr++ != '\n') {
				
			}
			break
		case 'a':
		case 'b':
		case 'c':
		case 'd':
		case 'e':
		case 'f':
		case 'g':
		case 'h':
		case 'i':
		case 'j':
		case 'k':
		case 'l':
		case 'm':
		case 'n':
		case 'o':
		case 'p':
		case 'q':
		case 'r':
		case 's':
		case 't':
		case 'u':
		case 'v':
		case 'w':
		case 'x':
		case 'y':
		case 'z':
		case 'A':
		case 'B':
		case 'C':
		case 'D':
		case 'E':
		case 'F':
		case 'G':
		case 'H':
		case 'I':
		case 'J':
		case 'K':
		case 'L':
		case 'M':
		case 'N':
		case 'O':
		case 'P':
		case 'Q':
		case 'R':
		case 'S':
		case 'T':
		case 'U':
		case 'V':
		case 'W':
		case 'X':
		case 'Y':
		case 'Z':
		case '_':
			ppos = ptr + 1;
			while (*ppos != '\0') {
				if (all_c.count(*ppos) > 1) {
					ppos += 1;
				} else {
					break;
				}
			}
			if (match(ppos, "operator")) {
				while (*ppos == ' ' || *ppos == '\t' ||  *ppos == '\n'||  *ppos == '\r') {
					ppos += 1;
				}
				if (*ppos == '(' && *(ppos+1) == ')') {
					ppos += 2;
				} else if (*ppos == '<' || *ppos == '>') {
					ppos += 1;
				}
			}
			ptr = ppos;
			break;
		default:
			ptr += 1;
		}
	}
	return -1;
}


PYBIND11_MODULE(tools, m) {
    m.doc() = "pybind11 example plugin"; // optional module docstring

    m.def("find", &find, "int find(char* ptr, int size, int pos)");
}