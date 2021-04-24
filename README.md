# A Tool to categorize and prioritize github issues
## Motivation
- Most of the github repositories have a huge number of issues which makes it difficult for the software developers and owners of the repository  to find issues that need to be addressed immediately.

- This workload can be reduced by dividing the issues into categories namely development, security, documentation and few others.

- Along with categorizing, prioritizing the issues in those categories would make the work easier.

## How to prioritize ?
- assign weightage to the issues.

- based on their importance like -
security related issues > bugs > enhancement > documentation > question > other

- un-assigned issues > assigned issues

- based on author association (owner > member > collaborator > contributor)

- based on discussion on issues (number of comments)

## Work done
### we had made an attempt in order to prioritize tensorflow issues
- in tensorflow we have mainly six categories - bugs, docs-bug, feature, build/install, performance and support
- we also have some unlabeled issues for which we can predict a label out of above six label
- for this we took naive-bayes classifier and trained it based on closed issues of tensorflow
- till this step evry issues got an label so now we can put them in six category
- we have put them in order and for the same we had assigned some weitage to each issue
 bugs (0.5) > features(0.4) > build/install(0.3) > docs-bug(0.2) > performance(0.1) > support(0.0)
- now these weitage can be increased on different criteria, we had took some
- we had kept unassigned issues first, so manager of the repo can assign these to someone because no one is working on them before.
- we can increased some weitage based on amount of conversation, if number of comment are increasing rapidly then it can be savere issues and contributeres are not able to resolve them.
- even though anyone can make severe issues but we have give some weitage based on author association also.

### please note this is just step in order to prioritizing issues even all the criteria can be wrong.

## how to run
- clone the repository in your local system
- open terminal in VSCode in GIP folder
- run the command - .\env\Scripts\activate.ps1
- and then - python .\app.py
- ctrl+click on the link or open port 5000 in broser
