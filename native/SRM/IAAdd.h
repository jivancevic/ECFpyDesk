#ifndef IAAdd_h
#define IAAdd_h

#include "ecf/tree/Add.h"
#include "IAPrimitive.h"

class IAAdd : public Tree::Primitives::Add, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
};

#endif // IAAdd_h
