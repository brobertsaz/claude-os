# Block System Deprecation Strategy

**Status**: Research & Planning Phase
**Date**: 2025-10-24
**Purpose**: Plan migration from custom Block templating engine to standard Rails views

---

## Current Block System Architecture

### What Are Blocks?

Blocks are PISTN's custom templating layer that allows CSRs to modify dealer-specific HTML/CSS/JS without code changes.

**Core Components**:
- **Block.rb** (1014 lines) - Hierarchical rendering engine
- **BlockSetting.rb** - Configuration & image handling
- **blocks.js** - Frontend behaviors
- **Admin UI** - Block editor interface

### How Blocks Work

#### 1. Hierarchical Structure (acts_as_tree)
```ruby
# Parent-child relationship with roles
parent_block
  ├── child_block (role: "header")
  ├── child_block (role: "content")
  └── child_block (role: "footer")
```

#### 2. Template Substitution ({{...}} syntax)
```html
<!-- Variable substitution -->
<h1>{{account.name}}</h1>

<!-- Conditional logic -->
{{if account.has_appointments?}}
  <div>{{yield.appointments}}</div>
{{/if}}

<!-- Ternary -->
{{account.is_active? ? 'Open' : 'Closed'}}

<!-- Loops -->
{{yield.services.each do |service|}}
  <div>{{service.name}}</div>
{{/yield.services.each}}
```

#### 3. Whitelist Security
```ruby
# Only whitelisted methods can be called
WHITELIST = {
  'account' => %w(name phone_number services ...),
  'block' => %w(image_url ...),
  'ANY' => %w(present? blank? to_s zero?)
}
```

#### 4. Account-Specific Content
- Universal blocks: `account_id = NULL`
- Account-specific: `account_id = specific_account`
- Group inheritance: Accounts inherit parent group's blocks
- Priority: Account-specific > Group > Universal

---

## Why Deprecate Blocks?

### Pain Points

#### Developer Experience
- ❌ 1000+ lines of state machine rendering logic
- ❌ Three languages in one file: HTML + Handlebars + Ruby
- ❌ No IDE support (syntax highlighting, autocomplete)
- ❌ Difficult to debug template logic

#### Maintenance & Testing
- ❌ Complex caching logic (cache invalidation bugs)
- ❌ Hard to unit test (requires full render context)
- ❌ N+1 query potential in template evaluation
- ❌ Security audits need constant whitelist review

#### Performance
- ❌ Interpretation layer (regex parsing, method lookup)
- ❌ Heavy context object passing
- ❌ Caching complexity adds overhead

#### User Experience (CSRs)
- ❌ Admin UI for block editing is clunky
- ❌ Learning curve (handlebars syntax)
- ❌ No real-time preview
- ❌ Error messages unhelpful

#### Architecture
- ⚠️ **Views Still Required**: Rails views exist anyway (blocks are a layer on top)
- ⚠️ **Duplication**: Both block template + Rails view exist
- ⚠️ **Migration Complexity**: Must maintain dual rendering for transition

---

## Migration Strategy

### Phase 1: Analysis & Mapping (Current)

**Tasks**:
1. ✅ Understand Block.rb rendering engine (done)
2. Identify all active blocks in production
3. Categorize blocks:
   - Simple HTML passthrough
   - Moderate complexity (some conditionals)
   - Complex (loops, dynamic content)
4. Map each block to Rails view equivalent
5. Document {{}} syntax usage patterns
6. Identify which blocks use advanced features

**Block 112 Case Study** (Appointment Form):
```
TODO: Query production database
- Block structure
- {{}} syntax patterns
- Block settings used
- Conditional rendering logic
- Child blocks/context
```

### Phase 2: Create Replacement Views

**For Each Block Type**:

1. **Create Rails Partial/View**
   ```erb
   <!-- app/views/account_specific/_appointment_form.html.erb -->
   <%= form_for @appointment do |f| %>
     <%= f.text_field :date %>
     <%= f.text_field :time %>
     <%= f.submit %>
   <% end %>
   ```

2. **Move Whitelist Logic to Presenter**
   ```ruby
   # app/presenters/account_presenter.rb
   class AccountPresenter
     def initialize(account)
       @account = account
     end

     def appointment_link
       # Only include if account has appointments enabled
       link_to "Book Appointment", appointment_path if @account.appointments_enabled?
     end
   end
   ```

3. **Use Rails Helpers**
   - Form helpers (form_for, form_with)
   - Link helpers (link_to, button_to)
   - Conditional helpers (if, unless)
   - Loop helpers (each, collect)

### Phase 3: Gradual Migration

**Feature Flag Approach**:

```ruby
# config/initializers/feature_flags.rb
FEATURE_FLAGS = {
  use_rails_views: false  # Start as false, enable per account
}

# In views/controllers
if account.use_rails_views?
  render :appointment_form_v2
else
  render_block(112)  # Old block system
end
```

**Per-Account Migration**:
- Add boolean `use_rails_views` to Account model
- Gradual rollout: test accounts → all dealers
- Monitor performance & error rates
- Easy rollback if issues

### Phase 4: Decommission

**Remove Block System**:
1. Delete Block rendering code
2. Remove block admin UI
3. Drop blocks/block_settings tables
4. Delete Block & BlockSetting models
5. Remove {{}} template syntax processor
6. Clean up views that use render_block()

---

## Implementation Steps

### Step 1: Research & Planning
- [ ] Query block 112 from production
- [ ] Document all {{}} patterns used
- [ ] Identify all active blocks
- [ ] Categorize by complexity
- [ ] Create mapping document

### Step 2: Build Replacement Views
- [ ] Create V2 views in app/views/account_specific/
- [ ] Create presenters in app/presenters/
- [ ] Move authorization logic to policies
- [ ] Create helpers for common patterns

### Step 3: Feature Flag & Testing
- [ ] Add `use_rails_views` to Account
- [ ] Implement feature flag logic
- [ ] Test with sample accounts
- [ ] Performance testing
- [ ] Error monitoring

### Step 4: Rollout
- [ ] Internal team testing
- [ ] Beta test with select dealers
- [ ] Gradual rollout to all accounts
- [ ] Monitor metrics
- [ ] Collect feedback

### Step 5: Cleanup
- [ ] Remove block system code
- [ ] Delete admin UI
- [ ] Drop database tables
- [ ] Update documentation

---

## Benefits After Migration

| Aspect | Before (Blocks) | After (Rails Views) |
|--------|-----------------|-------------------|
| **Code** | Custom 1000+ line engine | Standard Rails patterns |
| **Language** | HTML + Handlebars + Ruby | ERB only |
| **Testing** | Integration tests required | Standard view tests |
| **IDE** | No support | Full syntax highlighting |
| **Performance** | Interpretation layer | Direct rendering |
| **Security** | Massive whitelist | Rails authorization |
| **Debugging** | Context tracing | Standard stack traces |
| **CSR UX** | Block admin UI | Standard Rails admin (ActiveAdmin, etc) |
| **Onboarding** | Learn handlebars syntax | Standard Rails knowledge |

---

## Risk Mitigation

### Risks

**Performance**: Template rendering much slower?
- Mitigation: Rails view caching (fragment caching, etags)
- Testing: Benchmark before/after

**Breaking Changes**: Block customizations that can't translate?
- Mitigation: Identify edge cases in Phase 1
- Fallback: Keep Block system for complex accounts

**CSR Disruption**: CSRs dependent on block editor?
- Mitigation: Train on new Rails admin interface
- Timeline: Gradual rollout (6+ months)

**Database Migration**: Data loss from dropping tables?
- Mitigation: Archive block data before deletion
- Backup: Keep block definitions in version control

### Contingency Plans

1. If too many blocks use advanced features:
   - Keep blocks for "legacy mode"
   - Migrate new features to Rails views
   - Hybrid approach long-term

2. If performance regression:
   - Implement aggressive view caching
   - Use Redis for cache
   - Defer to background jobs

3. If CSR adoption slow:
   - Extend timeline
   - Provide better training
   - Create CSR-facing abstraction layer

---

## Next Steps

1. **This Session**:
   - Query block 112 structure
   - Document current {{}} syntax patterns
   - Identify block complexity categories

2. **Next Session**:
   - Create first V2 view (appointment form)
   - Build presenter/helper structure
   - Implement feature flag logic

3. **Future**:
   - Beta testing with select accounts
   - Performance optimization
   - Full rollout plan

---

## Resources

- Block.rb: 1014 lines, rendering logic in `render()` and `subbed_content()`
- BlockSetting.rb: Configuration and image handling
- BLOCKS_SYSTEM_GUIDE.md: Comprehensive architecture documentation
- Database: blocks, block_settings, accounts tables

---

**Status**: Ready for Phase 1 Analysis
**Owner**: Engineering Team
**Timeline**: 3-6 months estimated
