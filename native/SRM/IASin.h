#ifndef IASin_h
#define IASin_h

#include "ecf/tree/Sin.h"
#include "IAPrimitive.h"

class IASin : public Tree::Primitives::Sin, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
};

#endif // IASin_h
