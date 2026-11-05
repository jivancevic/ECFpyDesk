#ifndef IAERCD_h
#define IAERCD_h

#include "ecf/tree/Terminal.h"
#include "ecf/tree/Primitive.h"
#include "IAPrimitive.h"

class IAERCD : public Tree::Primitives::ERCD, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);

	Tree::PrimitiveP assignToNode(Tree::PrimitiveP primitive)
	{
		// shallow copy - the values_ are not copied
		IAERCD *erc = new IAERCD(*this);

		// generate a random value in the interval
		if(useInterval_) {
			double r = state_->getRandomizer()->getRandomDouble();
			erc->value_ = (*values_)[0] + r * ((*values_)[1] - (*values_)[0]);
		}
		// or choose a random predefined value
		else {
			uint iData = state_->getRandomizer()->getRandomInteger((int)values_->size());
			erc->value_ = values_->at(iData);
		}
		std::ostringstream ss;
		ss << erc->value_;
		erc->setName(name_ + ss.str());
		return (Tree::PrimitiveP) erc;
	}
};

typedef std::shared_ptr<IAERCD> IAERCDP;

#endif // IAERCD_h
