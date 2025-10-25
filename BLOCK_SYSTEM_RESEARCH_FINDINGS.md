# PISTN Block System Research - Complete Analysis

**Date**: 2025-10-24
**Status**: Comprehensive production analysis completed

---

## What Are Blocks?

Blocks are PISTN's custom templating engine that allows CSRs (Customer Service Representatives) to create dealer-specific HTML/CSS/JavaScript without code changes. They use a hierarchical structure with `{{variable}}` handlebars-style syntax.

## Key Findings from Production Analysis

### Block 122: Tuffy Appointment Form
- **Size**: 43KB (~1,150 lines)
- **Complexity**: Enterprise-grade form with 4-step wizard
- **Features**:
  - Multi-step form with client-side state management
  - Inline JavaScript (600+ lines)
  - jQuery UI Datepicker integration
  - Phone verification modal workflow
  - Existing vehicle lookup and selection
  - Google Tag Manager event tracking
  - 12+ conditional renders based on account settings
  - AJAX calls to fetch time slots

### Block Whitelist Security Model
- Massive whitelist of allowed methods (100+ entries) in Block.rb lines 54-137
- Examples: `account.name`, `account.online_scheduling_promo_message`, `account.use_mobile_verification`
- Security by whitelist is manageable but requires constant review

### Database Schema
```
blocks table:
- id, parent_id (hierarchical tree)
- role (semantic: "header", "content", "footer", etc.)
- tag (type classification)
- content (HTML + Handlebars template)
- account_id (NULL = universal, specific = account-only)
- position (float for ordering)
- attrs_data (JSON config)
- editable, wysiwyg, library flags
```

## Why Block 122 Matters

Block 122 represents the **maximum complexity** in PISTN's Block system:
- Multi-step form wizard
- Complex JavaScript behavior
- Account-specific customizations
- Feature flags (phone verification, towing, address fields, costco membership)
- State management across 4 steps
- Form field synchronization to confirmation display

**If Block 122 can be successfully migrated to Rails views, ANY block can be migrated.**

## Migration Strategy Summary

### High-Level Approach
1. **Decompose** the monolithic Block into Rails components
   - View partials for each form step
   - Presenter for data preparation
   - Service classes for validation
   - Stimulus controller for JavaScript

2. **Modernize** from inline JavaScript to standard Rails patterns
   - Extract 600+ lines to external Stimulus controller
   - Replace jQuery with standard fetch API
   - Use Rails form helpers instead of raw HTML

3. **Enhance** with Rails conventions
   - Active Record validations
   - Authorization policies
   - Test coverage (unit + integration + E2E)

### 4-Phase Deprecation Plan
1. **Analysis** (in progress): Map all blocks, categorize by complexity ✅
2. **Create Views**: Build Rails replacements (8 weeks per block)
3. **Gradual Migration**: Feature flags, per-account rollout
4. **Decommission**: Remove Block system, clean up database

## Key Technical Insights

### Block.rb Rendering Engine (1014 lines)
- `render(opts)`: Main orchestrator (lines 300-426)
- `subbed_content(opts)`: Template substitution engine for {{}} syntax (lines 436-599)
- `eval_bool(str, opts)`: Evaluate boolean expressions (lines 642-678)
- `eval_str(str, opts)`: Evaluate string expressions with dot notation (lines 680-752)

### Account-Specific Inheritance
- Blocks can be universal (account_id = NULL)
- Or account-specific (account_id = specific account)
- Inheritance: Account-specific > Group > Universal
- Caching layer adds complexity and potential for cache invalidation bugs

### Pain Points Identified
1. **Developer Experience**: 1000+ lines of state machine rendering logic
2. **Maintenance**: Complex caching, N+1 query potential, hard to test
3. **Performance**: Interpretation layer overhead
4. **CSR UX**: Admin UI is clunky, no real-time preview
5. **Architecture**: Views required anyway (blocks are extra layer)

## What We Now Know About Block 122

### HTML Structure
- 4-step wizard form with Bootstrap classes
- Multi-column layout (8-col form + 4-col sidebar)
- Modal for phone verification
- Loading overlay for time slot fetching
- Responsive (mobile-first approach with d-none/d-lg-block)

### JavaScript Requirements
- Step navigation with validation
- Date picker with availability filtering
- Form field → confirmation display binding
- Phone verification with code entry
- Existing vehicle selection with lookup
- Service category loop with checkboxes
- Store hours validation
- Required field validation

### Conditional Rendering
- `account.use_mobile_verification` → Show phone verification section
- `account.show_towing` → Show towing field
- `account.require_addr_for_appt` → Show address fields
- `account.require_costco_membership_number` → Show costco membership field
- `account.render_new_appt_times_string` → Filter calendar or show time dropdown

### Data Bindings
- Form fields sync to confirmation display on change
- Service selections update confirmation service list
- Vehicle selection updates vehicle display
- Date/time selections update confirmation
- Customer name, email, phone update throughout

## Implementation Insights

### Presenter Class Benefits
```ruby
class AppointmentFormPresenter
  # Replaces whitelist logic
  def show_financing_section?; end
  def use_mobile_verification?; end
  def require_address?; end
  # Clear, testable business logic
end
```

### Service Layer Pattern
```ruby
class ValidateAppointmentService
  def perform(account, step, data)
    # Complex validation logic
    # Returns { valid: true/false, errors: [...] }
  end
end
```

### View Decomposition
Instead of 1,150-line monolithic block:
- 120-line main form wrapper
- 80-line step 1 (services)
- 90-line step 2 (date/time)
- 110-line step 3 (customer info)
- 100-line step 4 (confirmation)
- 60-line modal (phone verification)
- Much more readable and testable

## Testing Strategy for Block 122

### Unit Tests (Service Layer)
- Validation logic for each step
- Date validation rules
- Store hours checks
- Phone verification flow
- Vehicle selection logic

### View Tests (Presenter + Partial)
- Conditional sections render correctly
- Form fields present
- Confirmation displays correct data
- Error messages display

### Integration Tests (Controller)
- Multi-step form flow
- AJAX calls (time slots, phone verify)
- Form submission success
- Database state after creation

### E2E Tests (Capybara)
- Complete user flow through all 4 steps
- Phone verification workflow
- Existing vehicle selection
- Error scenarios and retries
- Cross-browser compatibility

## Estimated Effort

- **Presenter + Controller**: 2 days
- **View Partials**: 3 days
- **JavaScript Extraction & Validation**: 5 days
- **Service Classes**: 3 days
- **Testing**: 5 days
- **Bug Fixes & Polish**: 2 days

**Total**: ~3-4 weeks for one block (block 122)
**With learnings applied to subsequent blocks**: 1 week per block

## Next Steps

1. ✅ Complete architectural analysis (done)
2. Create feature flag infrastructure in Rails
3. Build Presenter class for Block 122
4. Create view partials with code examples
5. Extract JavaScript to Stimulus controller
6. Build validation services
7. Create test suite (unit + integration + E2E)
8. Deploy to test account with feature flag
9. Beta test and iterate
10. Gradual rollout to all accounts

## Key Takeaway

**Block 122 is not just a form - it's a complete SPA (Single Page Application) embedded in the Block system.**

Migrating it to Rails views means:
- Taking the logic out of the Block interpreter
- Using proper Rails patterns (presenters, services, partials)
- Making it testable and maintainable
- Enabling future enhancements

The migration is complex but **entirely feasible** and will result in cleaner, more maintainable code.

---

## Related Documents

- `BLOCKS_DEPRECATION_STRATEGY.md` - 4-phase migration plan
- `BLOCK_CASE_STUDY_TUFFY_APPOINTMENT_FORM.md` - Complete Block 122 analysis with code
