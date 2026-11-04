#ifndef IASub_h
#define IASub_h

#include "ecf/tree/Sub.h"
#include "IAPrimitive.h"

class IASub : public Tree::Primitives::Sub, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
};

#endif // IASub_h
