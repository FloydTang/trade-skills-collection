## [LRN-20260325-001] 外贸 Skill 仓库采用双轨发布

**Logged**: 2026-03-25T00:00:00+08:00
**Priority**: high
**Status**: promoted
**Promote-To**: AGENTS.md

### Summary
外贸 Skill 后续默认采用“单节点独立仓库 + 合集仓库”的双轨发布结构。

### Details
单节点 Skill 独立仓库作为主开发源，适合快速迭代和单点发布。合集仓库作为分发与演示仓库，只收录已经达到“可演示”或“可交付”的稳定版本，方便用户一键下载和课程交付。

### Suggested Action
后续新增 Skill 时，先按独立节点完成立项、开发和验收；达到收录标准后，再同步到合集仓库。

## [LRN-20260325-002] 合集仓库优先保证完整下载体验

**Logged**: 2026-03-25T00:00:00+08:00
**Priority**: high
**Status**: promoted
**Promote-To**: README.md

### Summary
合集仓库中的节点 Skill 应优先保留完整目录副本，而不是依赖 submodule。

### Details
submodule 更适合开发协作，但不适合普通用户直接下载 ZIP 或课程交付。对于当前外贸 Skill 合集仓库，应优先保证用户下载后就能拿到完整内容。

### Suggested Action
后续收录进合集仓库的稳定节点，默认保留完整副本；独立仓库继续承担快速迭代。
