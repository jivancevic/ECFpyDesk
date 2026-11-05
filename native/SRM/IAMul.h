#ifndef IAMul_h
#define IAMul_h

#include "ecf/tree/Mul.h"
#include "IAPrimitive.h"

class IAMul : public Tree::Primitives::Mul, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
};

#endif // IAMul_h
