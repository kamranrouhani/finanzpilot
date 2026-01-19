# Phase 3: Budgets, AI Features & Polish

## Objective
Add budget management, AI-powered insights, receipt-transaction linking, and natural language queries.

## Prerequisites
- [ ] Phase 1 and Phase 2 completed and verified
- [ ] All previous tests passing
- [ ] Finanzguru data imported successfully
- [ ] Some receipt images uploaded

## Duration Estimate
- Ralph loop: 50-70 iterations
- Time: 8-12 hours (overnight run)
- API cost estimate: $50-100

## Deliverables

### D1: Budget Management
- [ ] Budget model and migration
- [ ] Budget CRUD endpoints
- [ ] Monthly/weekly/yearly periods
- [ ] Budget vs actual calculation
- [ ] Rollover support (optional)
- [ ] Budget alerts (threshold warnings)
- [ ] Tests for budget logic

### D2: Budget UI
- [ ] Budget list page
- [ ] Create/edit budget form
- [ ] Progress bars with color coding
- [ ] Category spending breakdown within budget
- [ ] Historical budget performance

### D3: Receipt-Transaction Linking
- [ ] Match receipts to transactions (date + amount)
- [ ] Manual linking UI
- [ ] Auto-suggest matches
- [ ] View receipt from transaction
- [ ] Tests for matching logic

### D4: AI Category Suggestions
- [ ] Analyze transaction for category
- [ ] Bulk categorization endpoint
- [ ] Confidence scores
- [ ] Learning from user corrections
- [ ] Category rules auto-creation
- [ ] Tests with mock Ollama

### D5: AI Insights
- [ ] Spending pattern analysis
- [ ] Anomaly detection (unusual expenses)
- [ ] Savings recommendations
- [ ] Monthly summary generation
- [ ] Tax-relevant expense identification
- [ ] Insights dashboard widget

### D6: Natural Language Queries
- [ ] Chat endpoint with context
- [ ] Query transaction data
- [ ] "How much did I spend on X in Y?"
- [ ] "Compare this month to last month"
- [ ] Chat UI component
- [ ] Tests for query parsing

### D7: Polish & Refinement
- [ ] Loading states throughout
- [ ] Error boundaries
- [ ] Toast notifications
- [ ] Keyboard shortcuts
- [ ] Mobile responsiveness check
- [ ] Performance optimization

### D8: Final Documentation
- [ ] User guide in README
- [ ] API documentation complete
- [ ] `docs/iterations/PHASE_3_COMPLETE.md`
- [ ] Known issues and limitations

## Ralph Loop Prompt

```
/ralph-loop:ralph-loop "
## Context
You are building FinanzPilot Phase 3: Budgets, AI Features & Polish.
Read @CLAUDE.md for project context.
Read @docs/SPEC.md for specifications.
Phases 1-2 complete: auth, receipts, transactions, dashboard work.

## Current Phase Objective
Add budgets, AI insights, receipt linking, natural language queries.

## AI Integration Notes
- Use Ollama at OLLAMA_HOST environment variable
- Vision model: qwen2.5-vl:7b (for receipts)
- Text model: qwen2.5:7b (for analysis, chat)
- Always handle Ollama connection errors gracefully
- Cache AI responses where appropriate

## Working Rules
1. Build on existing code - don't recreate
2. Write tests FIRST
3. Mock Ollama in tests (don't require real model)
4. Commit after each feature
5. Run full test suite before marking complete

## Git Workflow
1. Create branch: feature/phase-3
2. Commit after each feature
3. Run: make test before committing
4. Create PR when all deliverables complete

## Task Order (follow strictly)
1. Create Budget model + migration
2. Write budget CRUD tests
3. Implement budget endpoints
4. Write budget calculation tests
5. Implement budget vs actual logic
6. Build budget list and form UI
7. Build budget progress visualization
8. Write receipt-transaction matching tests
9. Implement auto-match logic
10. Build linking UI in transaction detail
11. Write AI categorization tests (mock Ollama)
12. Implement AI category suggestion endpoint
13. Implement bulk categorization
14. Write AI insights tests
15. Implement insights generation
16. Build insights widget
17. Write natural language query tests
18. Implement chat endpoint
19. Build chat UI component
20. Add loading states and error handling
21. Add toast notifications
22. Test mobile responsiveness
23. Write comprehensive E2E tests
24. Write PHASE_3_COMPLETE.md
25. Update README with user guide

## AI Prompts to Use

### Category Suggestion
'Based on this transaction, suggest a category:
Counterparty: {counterparty}
Description: {description}  
Amount: {amount} EUR
Respond with JSON only: {\"category\": \"...\", \"subcategory\": \"...\", \"confidence\": 0.0-1.0, \"tax_category\": \"...\" or null}'

### Spending Insights
'Analyze this spending data and provide insights in JSON:
{spending_summary}
Respond with: {\"insights\": [...], \"anomalies\": [...], \"recommendations\": [...]}'

### Natural Language Query
'You are a financial assistant. Answer based on this data:
{context}
Question: {question}
If the question requires calculation, show your work.
Answer in the same language as the question.'

## Verification Checklist
- [ ] Can create and track budgets
- [ ] Budget progress updates correctly with new transactions
- [ ] Can link receipt to transaction
- [ ] AI suggests reasonable categories
- [ ] Insights widget shows meaningful data
- [ ] Chat answers questions about spending
- [ ] All tests pass (including E2E)
- [ ] No console errors
- [ ] Works on mobile viewport

## If Stuck
- For Ollama mock: use unittest.mock or pytest-mock
- For budget calculation: aggregate transactions by category + period
- For chat context: include recent transactions summary, not all data
- For insights: focus on month-over-month comparison

## Output
When ALL deliverables complete and verified:
<promise>PHASE_3_COMPLETE</promise>
" --max-iterations 70 --completion-promise "PHASE_3_COMPLETE"
```

## Manual Verification After Ralph

### 1. Test Budgets
```bash
# Create budget
curl -X POST http://localhost:8000/api/budgets \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"category_id": "<uuid>", "amount": 500, "period": "monthly"}'

# Get budget summary
curl http://localhost:8000/api/budgets/summary \
  -H "Authorization: Bearer <token>"
```

### 2. Test Receipt Linking
1. Open transaction detail
2. Click "Link Receipt"
3. Should see suggested matches
4. Select receipt and confirm
5. Receipt should appear in transaction detail

### 3. Test AI Categorization
```bash
# Get category suggestion
curl -X POST http://localhost:8000/api/ai/categorize \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"counterparty": "REWE", "description": "REWE SAGT DANKE", "amount": -45.67}'
```

### 4. Test Chat
```bash
# Ask a question
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "How much did I spend on groceries last month?"}'
```

### 5. Full E2E Test
```bash
# Run Playwright tests
cd frontend
npx playwright test
```

### 6. Mobile Test
1. Open Chrome DevTools
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test iPhone 12 Pro viewport
4. Verify all pages usable

## Potential Issues & Solutions

| Issue | Solution |
|-------|----------|
| Ollama timeout | Increase timeout, add retry logic |
| AI hallucination | Add validation, confidence threshold |
| Budget calculation slow | Add database indexes, cache results |
| Chat context too large | Summarize transactions, limit history |
| Mobile layout broken | Check Tailwind responsive classes |

## AI Response Handling

### Category Suggestion Response
```python
class CategorySuggestion(BaseModel):
    category: str
    subcategory: Optional[str]
    confidence: float  # 0.0 - 1.0
    tax_category: Optional[str]
    reasoning: Optional[str]

# Only auto-apply if confidence > 0.8
# Show suggestion UI if confidence > 0.5
# Manual categorization if confidence < 0.5
```

### Insights Response
```python
class SpendingInsight(BaseModel):
    type: str  # "increase", "decrease", "anomaly", "pattern"
    category: str
    message: str
    amount: Optional[float]
    comparison_period: Optional[str]

class InsightsResponse(BaseModel):
    insights: List[SpendingInsight]
    anomalies: List[dict]
    recommendations: List[str]
    summary: str
```

## Files Created This Phase

```
finanzpilot/
├── backend/
│   ├── alembic/versions/
│   │   └── 004_budgets.py
│   ├── app/
│   │   ├── features/
│   │   │   ├── budgets/
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── models.py
│   │   │   └── ai/
│   │   │       ├── router.py
│   │   │       ├── service.py
│   │   │       ├── schemas.py
│   │   │       ├── ollama_client.py
│   │   │       └── prompts.py
│   │   └── shared/
│   │       └── cache.py
│   └── tests/
│       ├── test_budgets.py
│       ├── test_ai.py
│       └── mocks/
│           └── ollama_mock.py
├── frontend/
│   ├── src/
│   │   ├── app/(dashboard)/
│   │   │   ├── budgets/
│   │   │   │   ├── page.tsx
│   │   │   │   └── new/page.tsx
│   │   │   └── chat/
│   │   │       └── page.tsx
│   │   ├── components/features/
│   │   │   ├── budgets/
│   │   │   │   ├── BudgetList.tsx
│   │   │   │   ├── BudgetForm.tsx
│   │   │   │   └── BudgetProgress.tsx
│   │   │   ├── ai/
│   │   │   │   ├── InsightsWidget.tsx
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   └── CategorySuggestion.tsx
│   │   │   └── receipts/
│   │   │       └── ReceiptMatcher.tsx
│   │   └── lib/api/
│   │       ├── budgets.ts
│   │       └── ai.ts
│   └── tests/
│       ├── components/
│       │   ├── budgets.test.tsx
│       │   └── ai.test.tsx
│       └── e2e/
│           ├── budgets.spec.ts
│           └── chat.spec.ts
├── docs/
│   ├── iterations/
│   │   └── PHASE_3_COMPLETE.md
│   └── USER_GUIDE.md
└── README.md (updated)
```

## Post-Phase 3: Project Complete

After Phase 3, you have a fully functional app:

### Features Summary
✅ User authentication
✅ Finanzguru XLSX import
✅ Transaction management with filters
✅ Receipt OCR and linking
✅ Category management (including German tax categories)
✅ Budget tracking
✅ AI-powered insights
✅ Natural language queries
✅ Dashboard with charts

### Maintenance Tasks
1. Regular database backups
2. Monitor Ollama memory usage
3. Update models as new versions release
4. Review and improve AI prompts based on usage

### Future Enhancements (Optional)
- Multi-user / family sharing
- Bank API integration (FinTS)
- Mobile app (React Native)
- ELSTER export for taxes
- Investment tracking

---

**Start command:**
```bash
cd ~/projects/finanzpilot
git checkout -b feature/phase-3
claude
# Then paste the Ralph loop prompt
```

## Final Merge to Main

After all phases complete:

```bash
# Merge Phase 3
git checkout main
git merge feature/phase-3

# Tag release
git tag -a v1.0.0 -m "FinanzPilot v1.0.0 - Initial Release"
git push origin main --tags

# Celebrate 🎉
```
