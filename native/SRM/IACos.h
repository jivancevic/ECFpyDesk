#ifndef IACos_h
#define IACos_h

#include "ecf/tree/Cos.h"
#include "IAPrimitive.h"

class IACos : public Tree::Primitives::Cos, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
};

#endif // IACos_h
