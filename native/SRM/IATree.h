#ifndef IATree_h
#define IATree_h

#include <ecf/tree/Tree.h>

namespace Tree {

class IATree : public Tree
{
public:
	bool boundsCalculated;

	IATree();
	IATree* copy();

protected:
	void initializeFirst(Tree* hometree);
};

typedef std::shared_ptr<IATree> IATreeP;

}

#endif // IATree_h
