#ifndef IASqrt_h
#define IASqrt_h

#include "Sqrt.h"
#include "IAPrimitive.h"

class IASqrt : public Tree::Primitives::Sqrt, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
};

#endif // IASqrt_h
