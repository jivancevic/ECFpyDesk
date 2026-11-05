#ifndef IATerminal_h
#define IATerminal_h

#include "ecf/tree/Terminal.h"
#include "IAPrimitive.h"

class IATerminal : public Tree::Primitives::Terminal, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
	double lowerBound;
	double upperBound;
};

typedef std::shared_ptr<IATerminal> IATerminalP;

#endif // IATerminal_h
