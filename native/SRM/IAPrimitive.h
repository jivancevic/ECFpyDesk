#ifndef IAPrimitive_h
#define IAPrimitive_h

#include<iostream>
#include "IATree.h"

typedef struct {
	bool isWithinBounds;
	
	bool isLowerBoundInclusive;
	double lowerBound;

	bool isUpperBoundInclusive;
	double upperBound;
} IABounds;

class IAPrimitive
{
public:
	virtual IABounds calculateBounds(Tree::IATree& tree) = 0;

	// Returns true if everything is ok and expression should be evaluated
	virtual bool calculateBoundsIfRootNode(void* result, Tree::Tree& tree) {
		Tree::IATree& iaTree = static_cast<Tree::IATree&>(tree);
		if (!iaTree.boundsCalculated) {
			// bounds haven't been calculated yet
			IABounds bounds = this->calculateBounds(iaTree);
			iaTree.boundsCalculated = true;
			tree.iNode_ = 0; // reset tree's node index pointer
			if (!bounds.isWithinBounds) {
				// tree not within bounds, delete expression
				double& arg = *(double*)result;
				arg = 1e14;
				return false;
			}
		}
		return true;
	}
};

typedef std::shared_ptr<IAPrimitive> IAPrimitiveP;

#endif // IAPrimitive_h
