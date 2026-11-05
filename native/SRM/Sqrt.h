#ifndef Sqrt_h
#define Sqrt_h

#include <ecf/tree/Primitive.h>

namespace Tree {
namespace Primitives {

/**
 * \ingroup tree genotypes primitives
 * \brief Sqrt function primitive (Tree genotype)
 */
class Sqrt : public Primitive
{
public:
	Sqrt(void);
	void execute(void* result, Tree& tree);
	~Sqrt(void);
};

}
}

#endif 