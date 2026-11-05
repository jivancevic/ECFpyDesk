#ifndef IALog_h
#define IALog_h

#include "Log.h"
#include "IAPrimitive.h"

class IALog : public Tree::Primitives::Log, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
};

#endif // IALog_h
