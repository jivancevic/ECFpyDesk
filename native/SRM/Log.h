#ifndef Log_h
#define Log_h

#include <ecf/tree/Primitive.h>

namespace Tree {
namespace Primitives {

/**
 * \ingroup tree genotypes primitives
 * \brief Log function primitive (Tree genotype)
 */
class Log : public Primitive
{
public:
	Log(void);
	void execute(void* result, Tree& tree);
	~Log(void);
};

}
}

#endif 