#ifndef IADiv_h
#define IADiv_h

#include "ecf/tree/Div.h"
#include "IAPrimitive.h"

class IADiv : public Tree::Primitives::Div, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
};

bool boundsContainZero(IABounds bounds);

#endif // IADiv_h
