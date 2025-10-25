# Block System Case Study: Tuffy Appointment Form (Block 122)
## Migration Blueprint for Rails Views Refactor

**Date**: 2025-10-24
**Block ID**: 122 (Tuffy Appt Main)
**Account ID**: 11187 (Account-specific block)
**Status**: Real production block analyzed

---

## Executive Summary

Block 122 is **THE complex appointment scheduling form** - representing the highest complexity in PISTN's Block system. It demonstrates:

- ✅ 43KB of mixed HTML, Handlebars templating, and inline JavaScript
- ✅ 4-step wizard workflow with client-side state management
- ✅ Complex conditional rendering based on account settings
- ✅ Inline JavaScript with jQuery and event handlers
- ✅ Form validation with business logic
- ✅ Multiple child block yields
- ✅ Data binding between form fields and confirmation display
- ✅ Phone verification modal workflow
- ✅ Google Tag Manager event tracking
- ✅ Existing vehicle lookup and selection

This block is a **stress test** for the migration strategy - if we can migrate Block 122 to Rails, we can migrate anything.

---

## Part 1: Block 122 Architecture Analysis

### Database Record

```
ID: 122
Name: Tuffy Appt Main
Tag: (empty)
Role: (empty)
Account ID: 11187 (Account-specific - not universal)
Parent ID: NULL (top-level block)
Content Length: 43,762 bytes (~44 KB)
```

### Key Statistics

- **Total Lines of Code**: ~1,150 lines (mixed HTML/JavaScript)
- **JavaScript Lines**: ~600 lines (inline, not external file)
- **HTML Structure**: Bootstrap grid-based 4-step wizard
- **Form Steps**:
  1. Service selection with service categories
  2. Date/time picker with calendar UI
  3. Customer information with vehicle selection
  4. Confirmation review
- **Form Fields**: 25+ input fields across all steps
- **Conditional Renders**: 12+ places using `{{ }}` handlebars syntax
- **Event Handlers**: 10+ JavaScript event listeners
- **API Endpoints**: Calls to `/verify_phone_number`, `/appointment` (form submit)

---

## Part 2: Detailed Structure Breakdown

### Data Dependencies

**Account-Level Properties Accessed**:
```javascript
// Via {{account.property}} syntax
account.id                                  // Account ID
account.name                                // Display name
account.address_str                         // Address
account.phone_number                        // Phone
account.online_scheduling_promo_message     // Promotional message
account.require_addr_for_appt               // Address field requirement
account.require_costco_membership_number?   // Costco membership requirement
account.show_towing                         // Towing field requirement
account.require_license_plate               // License plate requirement
account.use_mobile_verification             // Phone verification toggle
account.store_hours_options                 // Hour dropdowns (HTML options)
account.store_hours_html                    // Rendered hours display
account.render_new_appt_times_string        // Calendar filtering flag
account.appt_min_hours                      // Minimum hours before appointment
```

**Page Object**:
```javascript
page.intro_or_default_text                  // Customizable intro copy
```

**Model-Level Properties**:
```javascript
account.visible_service_categories          // yield: Service category loop
account.account_services                    // yield: Services within category
```

### Form Structure

```
Appointment Form (id="appt_form")
├── Step 1: Service Selection
│   ├── {{yield account.visible_service_categories}}  → Loop through categories
│   ├── Wait/Drop-off dropdown
│   └── Submit: "Select date/time"
│
├── Step 2: Date & Time
│   ├── jQuery UI Datepicker calendar
│   ├── Phone Verification Section (conditional on use_mobile_verification)
│   ├── Preferred Time dropdown ({{account.store_hours_options}})
│   ├── Towing dropdown (conditional on account.show_towing)
│   └── Submit: "Enter your information"
│
├── Step 3: Customer Information
│   ├── Personal Info (first name, last name, email, phone)
│   ├── Costco Membership (conditional on require_costco_membership_number)
│   ├── {{yield Address Fields if account.require_addr_for_appt}}
│   ├── Vehicle Selection
│   │   ├── Existing Vehicles List (populated by JavaScript)
│   │   └── {{yield New Veh Form}} (for new vehicles)
│   ├── Car Issues textarea
│   └── Submit: "Confirm your Appointment Request"
│
├── Step 4: Confirmation
│   ├── Summary Review
│   │   ├── Customer Name & Vehicle
│   │   ├── Location ({{account.name}}, {{account.address_str}})
│   │   ├── Services
│   │   ├── Date/Time
│   │   └── Notes
│   ├── {{yield TuffySignUps}} (right sidebar)
│   ├── Recaptcha box
│   └── Submit: "Request Appointment"
│
└── Modal: Phone Verification
    ├── Input: Verification code
    ├── Actions: Verify Code, Resend Code
    └── Status messages
```

### JavaScript Functions (Critical to Migration)

```javascript
window.choose_step(stepNum)
  // Navigate between form steps
  // Updates UI, scrolls to top, shows/hides sidebars
  // Core: $('.form-step').hide(); $(`#form-step-${i}`).show();

window.validate_step(stepNum)
  // Complex validation logic including:
  // - Required field checking
  // - Special vehicle selection logic (existing vs new)
  // - Date validation (must be 24+ hours from now)
  // - Store hours validation
  // - Phone verification check (if enabled)
  // - Google Tag Manager event firing

window.set_confirm()
  // Updates confirmation display when fields change
  // Binds to: input[name="services[]"], input[name="customer[*]"]

window.updateConfirmationStep()
  // Updates step 4 confirmation with selected vehicle

window.verifyPhoneNumber(accountId, number)
  // AJAX call to /verify_phone_number
  // Shows modal with verification code input
  // Expiry: 5 minutes

window.updateTimeSlots(dateStr, accountId, wait, selectedServiceIds)
  // AJAX: Fetches available time slots
  // Called when date selected IF render_new_appt_times_string == true

window.change_location()
  // Reopens location selection

window.validate_store_hours()
  // Checks if appointment time is within store hours
  // Uses window.active_hours array

window.removeSelectError / removeError
  // Event handlers for error removal on user input
```

### Child Block Yields

Block 122 references these child blocks via `{{yield ...}}`:

1. **{{yield account.visible_service_categories}}**
   - Loop through service categories
   - Each category has checkboxes for services
   - Calls `{{yield account.account_services}}` for services in category
   - Example: `yield Block 25342` (service selector)

2. **{{yield Address Fields if account.require_addr_for_appt}}**
   - Conditional address input block
   - Only shown if account.require_addr_for_appt is true

3. **{{yield New Veh Form}}**
   - New vehicle year/make/model selectors
   - Example: block 24794, 24793 (vehicle form blocks)

4. **{{yield TuffySignUps}}**
   - Newsletter signup on confirmation step
   - Example: block 2418 (empty placeholder)

---

## Part 3: Complexity Metrics

### Why Block 122 is High Complexity

| Factor | Score | Details |
|--------|-------|---------|
| **Size** | 9/10 | 43KB, ~1,150 lines |
| **JavaScript** | 10/10 | 600+ lines of inline JS, event handlers, AJAX |
| **Conditional Logic** | 7/10 | 12+ places with `if` conditions, feature flags |
| **State Management** | 9/10 | Multi-step wizard with complex validation |
| **Data Binding** | 8/10 | Form fields must sync with confirmation display |
| **External Dependencies** | 8/10 | jQuery UI Datepicker, reCAPTCHA, Google Tag Manager |
| **API Calls** | 6/10 | POST /appointment, GET /verify_phone_number, XHR for time slots |
| **Testing Difficulty** | 9/10 | Integration + E2E testing required for full coverage |

**Overall Complexity**: **8.5/10** - Enterprise-grade appointment form with sophisticated UX

---

## Part 4: Migration Strategy

### Approach: Decompose into Rails Components

Instead of replacing Block 122 directly, decompose into:

1. **Views** - Multi-step form partials
2. **Controller** - Step navigation, validation
3. **Service** - Business logic (validation, time slot fetching)
4. **Presenter** - Data preparation for views
5. **JavaScript** - Extract to external JS files

### File Structure

```
app/views/appointments/
├── _appointment_form.html.erb          # Main form wrapper
├── _step_1_services.html.erb           # Service selection
├── _step_2_datetime.html.erb           # Date/time picker
├── _step_3_customer_info.html.erb      # Personal info & vehicle
├── _step_4_confirmation.html.erb       # Review & submit
└── _phone_verification_modal.html.erb  # Phone verification modal

app/controllers/
└── appointments_controller.rb           # Step navigation, submission

app/presenters/
└── appointment_form_presenter.rb        # Data preparation, conditionals

app/services/
└── validate_appointment_service.rb      # Complex validation logic
└── fetch_appointment_slots_service.rb   # Calendar/slot fetching

app/assets/javascripts/
└── appointment_form.js                  # Extract inline JS here
```

### Step 1: Create Presenter

File: `app/presenters/appointment_form_presenter.rb`

```ruby
class AppointmentFormPresenter
  def initialize(account, appointment = nil)
    @account = account
    @appointment = appointment || Appointment.new
  end

  # Account properties
  def account_id; @account.id; end
  def account_name; @account.name; end
  def account_address; @account.address_str; end
  def account_phone; @account.phone_number; end

  # Conditionals
  def show_online_scheduling_promo?
    @account.online_scheduling_promo_message.present?
  end

  def online_scheduling_promo_message
    @account.online_scheduling_promo_message
  end

  def require_address?
    @account.require_addr_for_appt?
  end

  def require_costco_membership?
    @account.require_costco_membership_number?
  end

  def show_towing?
    @account.show_towing?
  end

  def use_mobile_verification?
    @account.use_mobile_verification?
  end

  def minimum_appointment_hours
    @account.appt_min_hours || 24
  end

  def filter_time_slots?
    @account.render_new_appt_times_string == 'true'
  end

  # Service categories (for yield loop)
  def visible_service_categories
    @account.visible_service_categories
  end

  # Store hours
  def store_hours_html
    @account.store_hours_html
  end

  def store_hours_options
    @account.store_hours_options
  end

  def store_hours_json
    # For JavaScript time validation
    @account.store_hours_for_js.to_json
  end

  # Intro text
  def intro_text
    Page.intro_or_default_text || "Schedule your appointment with us."
  end
end
```

### Step 2: Create Controller

File: `app/controllers/appointments_controller.rb`

```ruby
class AppointmentsController < ApplicationController
  before_action :set_account
  before_action :set_presenter, only: [:new]

  # Show appointment form
  def new
    @appointment = Appointment.new
    @presenter = AppointmentFormPresenter.new(@account)

    # For existing vehicles (pre-fill if customer found)
    @existing_vehicles = @account.vehicles.where(
      phone_number: params[:phone]
    ) if params[:phone].present?
  end

  # Handle step navigation (AJAX)
  def validate_step
    step = params[:step].to_i
    data = JSON.parse(params[:form_data] || '{}')

    result = ValidateAppointmentService.perform(
      account: @account,
      step: step,
      data: data
    )

    if result[:valid]
      render json: { valid: true }
    else
      render json: { valid: false, errors: result[:errors] }, status: :unprocessable_entity
    end
  end

  # Fetch available time slots
  def available_slots
    date = params[:date]
    services = params[:service_ids] || []
    wait_type = params[:wait]

    slots = FetchAppointmentSlotsService.perform(
      account: @account,
      date: date,
      service_ids: services,
      wait_type: wait_type
    )

    render json: { slots: slots }
  end

  # Verify phone number for existing customer lookup
  def verify_phone
    phone = params[:phone]
    result = VerifyPhoneService.perform(phone: phone)

    if result[:valid]
      # Send verification code (SMS/email)
      render json: {
        valid: true,
        verification_code: result[:code],  # For testing only
        expires_at: 5.minutes.from_now
      }
    else
      render json: { valid: false }, status: :unprocessable_entity
    end
  end

  # Create appointment
  def create
    service = CreateAppointmentService.perform(
      account: @account,
      customer_params: customer_params,
      appointment_params: appointment_params
    )

    if service.is_a?(Appointment)
      # Send confirmation email, etc.
      render json: { success: true, appointment_id: service.id }
    else
      render json: { success: false, error: service }, status: :unprocessable_entity
    end
  end

  private

  def set_account
    @account = current_account
  end

  def set_presenter
    @presenter = AppointmentFormPresenter.new(@account)
  end

  def customer_params
    params.require(:customer).permit(
      :first_name, :last_name, :email, :phone,
      :costco_membership_number
    )
  end

  def appointment_params
    params.require(:appointment).permit(
      :appointment_date, :appointment_time, :wait,
      :towing, :car_issues, :car_year, :car_make, :car_model,
      :service_ids => []
    )
  end
end
```

### Step 3: Create Views

#### File: `app/views/appointments/new.html.erb`

```erb
<%= render 'appointment_form', presenter: @presenter, existing_vehicles: @existing_vehicles %>
```

#### File: `app/views/appointments/_appointment_form.html.erb`

```erb
<article>
  <header class="brand-header condensed text-center pt-4 pb-4 pl-2 pr-2 pt-lg-5 pb-lg-4 pl-lg-4 pr-lg-4 d-flex flex-column align-items-center justify-content-center lazy lazyload"
          data-bg="/images/tuffy/header-quote.jpg">
    <h1 class="display-2 text-yellow text-uppercase">Schedule an Appointment</h1>
  </header>

  <section class="form-wrap pt-5 pb-5">
    <div id="apptLoadingModal" class="appt-modal-overlay" style="display:none;">
      <div class="appt-modal-content">
        <p>Fetching available times <span class="ellipsis"></span></p>
      </div>
    </div>

    <%= form_with url: appointments_path, method: :post, id: 'appt_form', local: true, class: 'container' do |f| %>
      <input type="hidden" id="account_id" value="<%= presenter.account_id %>">
      <input type="hidden" id="filterTimeSlots" value="<%= presenter.filter_time_slots? %>">
      <input type="hidden" id="customer_sent_message_id" name="customer[sent_message_id]">
      <input type="hidden" id="rwg_token" name="rwg_token">

      <noscript>JavaScript required for appointment scheduling</noscript>

      <div class="row">
        <!-- Form Steps Container -->
        <div class="col-12 col-lg-8">
          <!-- Step Progress Indicator -->
          <div class="form-steps d-none d-lg-block">
            <ul class="steps list-unstyled d-flex flex-row justify-content-between align-items-start mb-4 mt-2">
              <li class="h5 current text-uppercase"><span>Service(s)</span></li>
              <li class="h5 text-uppercase"><span>Date/Time</span></li>
              <li class="h5 text-uppercase"><span>Your Info</span></li>
              <li class="h5 text-uppercase"><span>Confirm</span></li>
            </ul>
          </div>

          <!-- Intro Text -->
          <div class="col-12 col-lg-8" style="text-align: justify;">
            <%= presenter.intro_text %>
          </div>

          <!-- Promo Message -->
          <% if presenter.show_online_scheduling_promo? %>
            <div class="col-12 col-lg-8" style="font-size:20px;font-weight:bold;text-align: justify;">
              <%= presenter.online_scheduling_promo_message %>
            </div>
          <% end %>

          <!-- Step 1: Service Selection -->
          <%= render 'step_1_services', presenter: presenter %>

          <!-- Step 2: Date & Time -->
          <%= render 'step_2_datetime', presenter: presenter %>

          <!-- Step 3: Customer Information -->
          <%= render 'step_3_customer_info', presenter: presenter, existing_vehicles: existing_vehicles %>

          <!-- Step 4: Confirmation -->
          <%= render 'step_4_confirmation', presenter: presenter %>
        </div>

        <!-- Right Sidebar (Signup) -->
        <div class="col-12 col-lg-5 h-100" id="sign-up-sidebar" style="display: none;">
          <div class="form-cta bg-yellow pl-3 pr-3 pt-4 pb-4 h-100 text-black">
            <!-- Signup section would go here -->
            <div id="recaptcha-box"></div>
            <%= submit_tag 'Request Appointment',
                          class: 'btn btn-lg btn-black text-yellow d-block w-100 text-center',
                          id: 'tuffyRequestApptBtn',
                          disabled: true %>
          </div>
        </div>

        <!-- Right Sidebar (Summary) -->
        <div class="col-12 col-lg-4 h-100" id="summary-sidebar">
          <div class="form-cta bg-black pl-3 pr-3 pt-4 pb-4 h-100">
            <h2 class="h3 text-uppercase text-yellow mb-4">Requested Appointment Summary</h2>
            <div class="form-group d-flex justify-content-between text-white pb-3 mb-3">
              <div class="content">
                <p class="mb-3 small">
                  <strong><%= presenter.account_name %></strong><br>
                  <%= presenter.account_address %><br>
                  <%= presenter.account_phone %>
                </p>
                <p class="m-0 small">
                  <strong>Hours of Operation</strong><br>
                  <ul style="list-style-type: none; padding-left: 0; font-size: 80%;" class="hours">
                    <%= raw presenter.store_hours_html %>
                  </ul>
                </p>
              </div>
              <a href="#" class="tiny text-yellow" onclick="window.change_location(); return false;">Change</a>
            </div>
          </div>
        </div>
      </div>

      <% if presenter.use_mobile_verification? %>
        <%= render 'phone_verification_modal' %>
      <% end %>
    <% end %>
  </section>
</article>

<!-- Initialize JavaScript -->
<script>
  document.addEventListener('DOMContentLoaded', function() {
    window.appointmentForm = new AppointmentForm({
      accountId: '<%= presenter.account_id %>',
      filterTimeSlots: <%= presenter.filter_time_slots?.to_s.titleize.downcase %>,
      usePhoneVerification: <%= presenter.use_mobile_verification?.to_s.titleize.downcase %>,
      minimumHours: <%= presenter.minimum_appointment_hours %>,
      storeHours: <%= raw presenter.store_hours_json %>
    });
  });
</script>
```

#### File: `app/views/appointments/_step_1_services.html.erb`

```erb
<div class="form-step col-12 col-lg-8 mb-5 mb-lg-0" id="form-step-1">
  <div class="form-flds-container bg-ltgray border">
    <!-- Service Categories Loop -->
    <% presenter.visible_service_categories.each do |category| %>
      <div class="service-category mb-4">
        <h3 class="h4 text-uppercase"><%= category.name %></h3>
        <div class="services-list">
          <% category.account_services.each do |account_service| %>
            <label class="d-flex align-items-center mb-2">
              <input type="checkbox"
                     name="appointment[service_ids][]"
                     id="service_<%= account_service.service.id %>"
                     value="<%= account_service.service.id %>"
                     class="service-checkbox mr-2">
              <span><%= account_service.service.name %></span>
            </label>
          <% end %>
        </div>
      </div>
    <% end %>

    <!-- Wait/Drop-off Selection -->
    <div class="form-flds-container bg-ltgray border mt-2">
      <label for="wait" class="h4 d-block text-uppercase p-2">
        Planning to wait or drop off? <span class="required">*</span>
      </label>
      <select id="wait" name="appointment[wait]" class="required w-100 border h4 p-2">
        <option value="">Select Wait/Drop Off</option>
        <option value="Wait">I will wait for my vehicle</option>
        <option value="Drop-Off">I will drop off my vehicle</option>
      </select>
    </div>
  </div>

  <div class="text-right pt-4">
    <button type="button"
            class="text-uppercase text-black btn btn-yellow btn-lg m-0 d-block w-100 pl-5 pr-5"
            id="apptSelectDateTimeBtn"
            onclick="window.appointmentForm.goToStep(2); return false;">
      Select date/time
    </button>
  </div>
</div>
```

#### File: `app/views/appointments/_step_2_datetime.html.erb`

```erb
<div class="form-step col-12 col-lg-8 mb-5 mb-lg-0" id="form-step-2" style="display: none;">
  <div class="form-flds-container bg-ltgray border pt-4 pb-4 pl-2 pr-2 p-lg-4">
    <div class="container full">
      <div class="row">
        <!-- Date Picker -->
        <div class="col-12 calendar-wrap-outer">
          <div class="calendar-wrap position-relative mt-2 mb-5 d-flex justify-content-center justify-lg-content-start align-items-center">
            <div id="date-select"></div>
            <input type="hidden" id="customer_appointment_date"
                   name="appointment[appointment_date]"
                   class="required">
          </div>
        </div>
      </div>

      <!-- Time Selection (conditional) -->
      <div class="row" id="selectHoursSection" style="display:none;">
        <div class="col-12 col-lg-4 mb-3 mb-lg-0">
          <label for="customer_appointment_time" class="h5 d-block text-uppercase">
            Preferred Time <span class="required">*</span>
          </label>
          <select id="customer_appointment_time"
                  name="appointment[appointment_time]"
                  class="w-100 border p-2 h4 required">
            <option>Select Time</option>
            <%= raw presenter.store_hours_options %>
          </select>
        </div>

        <% if presenter.show_towing? %>
          <div class="col-12 col-lg-4 mb-3 mb-lg-0">
            <label for="towing" class="h5 d-block text-uppercase">
              Will you need towing? <span class="required">*</span>
            </label>
            <select id="towing" name="appointment[towing]" class="w-100 border p-2 h4 required">
              <option value="">Select Towing</option>
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>
        <% end %>
      </div>

      <!-- Phone Verification (conditional) -->
      <% if presenter.use_mobile_verification? %>
        <div class="row mt-4" id="phoneVerificationSection" style="display:none;">
          <div class="col-12">
            <div class="form-group">
              <label for="customer_phone_step2" class="h5 d-block text-uppercase">
                Phone Number <span class="required">*</span>
              </label>
              <div class="d-flex">
                <input type="text" id="customer_phone_step2"
                       name="customer[phone]"
                       class="w-100 border p-2 h4 required"
                       style="margin-right: 10px;"
                       placeholder="Enter your phone number">
                <button type="button" id="verifyPhoneBtn" class="btn btn-yellow text-black" style="white-space: nowrap;">
                  <span id="verifyBtnText">Verify Phone</span>
                </button>
              </div>
              <div id="phoneVerificationStatus" class="mt-2" style="display: none;">
                <small class="text-success">Phone number verified</small>
              </div>
              <div id="customerFoundStatus" class="mt-2" style="display: none;">
                <small class="text-info">Customer found! We'll pre-fill your information in the next step.</small>
              </div>
            </div>
          </div>
        </div>
      <% end %>
    </div>
  </div>

  <div class="text-right pt-4">
    <button type="button"
            class="text-uppercase text-black btn btn-yellow btn-lg m-0 d-block w-100 pl-5 pr-5"
            id="apptEnterInformationBtn"
            onclick="window.appointmentForm.goToStep(3); return false;">
      Enter your information
    </button>
  </div>
</div>
```

#### File: `app/views/appointments/_step_3_customer_info.html.erb`

```erb
<div class="form-step col-12 col-lg-8 mb-5 mb-lg-0" id="form-step-3" style="display: none;">
  <div class="form-flds-container bg-ltgray border pl-4 pr-4 pt-5 pb-3">
    <input type="hidden" name="customer[form_submit]" value="true">

    <!-- Personal Info -->
    <div class="form-group d-block d-lg-flex">
      <div class="form-fld w-100 pr-lg-2 mb-3 mb-lg-0">
        <label for="customer_first_name" class="h5 d-block text-uppercase">
          First name <span class="required">*</span>
        </label>
        <input type="text" id="customer_first_name"
               name="customer[first_name]"
               class="w-100 border h4 p-2 required">
      </div>
      <div class="form-fld w-100 pr-lg-2 mb-3 mb-lg-0">
        <label for="customer_last_name" class="h5 d-block text-uppercase">
          Last name <span class="required">*</span>
        </label>
        <input type="text" id="customer_last_name"
               name="customer[last_name]"
               class="w-100 border h4 p-2 required">
      </div>
    </div>

    <!-- Contact Info -->
    <div class="form-group d-block d-lg-flex">
      <div class="form-fld w-100 pr-lg-2 mb-3 mb-lg-0">
        <label for="customer_email" class="h5 d-block text-uppercase">
          Email address <span class="required">*</span>
        </label>
        <input type="email" id="customer_email"
               name="customer[email]"
               class="w-100 border h4 p-2 required">
      </div>
      <div class="form-fld w-100 pr-lg-2 mb-3 mb-lg-0">
        <label for="customer_phone" class="h5 d-block text-uppercase">
          Phone number <span class="required">*</span>
        </label>
        <input type="text" id="customer_phone"
               name="customer[phone]"
               class="w-100 border h4 p-2 required">
        <small id="phoneVerifiedMessage" class="text-muted" style="display: none;">
          Phone number verified in previous step
        </small>
      </div>
    </div>

    <!-- Costco Membership (conditional) -->
    <% if presenter.require_costco_membership? %>
      <div class="form-group d-block d-lg-flex">
        <div class="form-fld w-100 pr-lg-2 mb-3 mb-lg-0">
          <label for="customer_costco_membership_number" class="h5 d-block text-uppercase">
            Costco Membership Number (if a member)
          </label>
          <input type="text" id="customer_costco_membership_number"
                 name="customer[costco_membership_number]"
                 class="w-100 border h4 p-2">
        </div>
      </div>
    <% end %>

    <!-- Address (conditional via yield) -->
    <% if presenter.require_address? %>
      <%= render 'address_fields' %>
    <% end %>

    <!-- Vehicle Selection -->
    <div class="form-group d-flex">
      <div class="form-fld w-100">
        <label for="vehicle" class="h5 d-block text-uppercase mb-3">
          Your vehicle <span class="required">*</span>
        </label>
        <fieldset>
          <!-- Existing Vehicles (conditional) -->
          <div id="existingVehiclesSection" style="display: none;">
            <div class="mb-3">
              <label class="h6 d-block text-uppercase mb-2">Select an existing vehicle:</label>
              <div id="existingVehiclesList" class="mb-3">
                <% if existing_vehicles.present? %>
                  <% existing_vehicles.each do |vehicle| %>
                    <label class="d-flex align-items-center mb-2">
                      <input type="radio" name="vehicle_selection"
                             value="existing_<%= vehicle.id %>" class="mr-2">
                      <span><%= "#{vehicle.year} #{vehicle.make} #{vehicle.model}" %></span>
                    </label>
                  <% end %>
                <% end %>
              </div>
              <div class="text-center">
                <button type="button" id="addNewVehicleBtn" class="btn btn-yellow text-black btn-sm">
                  + Add a different vehicle
                </button>
              </div>
            </div>
            <hr class="my-3">
          </div>

          <!-- New Vehicle Form -->
          <div id="newVehicleSection">
            <%= render 'vehicle_form' %>
          </div>
        </fieldset>
      </div>
    </div>

    <!-- Problem Description -->
    <div class="form-group d-flex">
      <div class="form-fld w-100">
        <label for="customer_car_issues" class="h5 d-block text-uppercase">
          Tell us a bit about your vehicle problem(s) <span class="required">*</span>
        </label>
        <textarea id="customer_car_issues"
                  name="appointment[car_issues]"
                  class="w-100 border h4 p-2 required"
                  style="height:10rem"></textarea>
      </div>
    </div>
  </div>

  <div class="text-right pt-4">
    <button type="button"
            class="text-uppercase text-black btn btn-yellow btn-lg m-0 d-block w-100 pl-5 pr-5"
            id="apptConfirmAppointmentBtn"
            onclick="window.appointmentForm.goToStep(4); return false;">
      Confirm your Appointment Request
    </button>
  </div>
</div>
```

#### File: `app/views/appointments/_step_4_confirmation.html.erb`

```erb
<div class="form-step col-12 col-lg-7" id="form-step-4" style="display: none">
  <div class="form-flds-container bg-ltgray border pl-4 pr-4 pt-5 pb-3">
    <h2 class="h1 mb-5">Does this look right?</h2>

    <!-- Customer & Vehicle Summary -->
    <div class="form-group d-flex justify-content-between text-black pb-3 border-bottom mb-3">
      <div class="content">
        <h3 class="h3 text-uppercase text-black mb-2">
          <span id="confirm_first_name"></span> <span id="confirm_last_name"></span><br>
          <span id="confirm_car_year"></span> <span id="confirm_car_make"></span>
          <span id="confirm_car_model"></span> <span id="confirm_car_option"></span>
        </h3>
        <p class="m-0">
          <span id="confirm_email"></span><br>
          <span id="confirm_phone"></span>
        </p>
      </div>
      <a href="#" class="small" onclick="window.appointmentForm.goToStep(3); return false;">Change</a>
    </div>

    <!-- Location Summary -->
    <div class="form-group d-flex justify-content-between text-black pb-3 border-bottom mb-3">
      <div class="content">
        <h3 class="h3 text-uppercase text-black mb-2">Location</h3>
        <p class="m-0">
          <strong><%= presenter.account_name %></strong><br>
          <%= presenter.account_address %><br>
          <%= presenter.account_phone %>
        </p>
      </div>
      <a href="#" class="small" onclick="window.appointmentForm.change_location(); return false;">Change</a>
    </div>

    <!-- Services Summary -->
    <div class="form-group d-flex justify-content-between text-black pb-3 border-bottom mb-3">
      <div class="content">
        <h3 class="h3 text-uppercase text-black mb-2">Services</h3>
        <p class="m-0" id="confirm_services"></p>
      </div>
      <a href="#" class="small" onclick="window.appointmentForm.goToStep(1); return false;">Edit</a>
    </div>

    <!-- Date/Time Summary -->
    <div class="form-group d-flex justify-content-between text-black pb-3 border-bottom mb-3">
      <div class="content">
        <h3 class="h3 text-uppercase text-black mb-2">Date/Time</h3>
        <p class="m-0">
          <span id="confirm_appointment_date"></span> @ <span id="confirm_appointment_time"></span>
          <br><span id="confirm_wait"></span>
          <% if presenter.show_towing? %>
            <br><span id="confirm_towing"></span> towing required
          <% end %>
        </p>
      </div>
      <a href="#" class="small" onclick="window.appointmentForm.goToStep(2); return false;">Edit</a>
    </div>

    <!-- Notes Summary -->
    <div class="form-group d-flex justify-content-between text-black pb-3">
      <div class="content">
        <h3 class="h3 text-uppercase text-black mb-2">Your notes</h3>
        <p class="m-0" id="confirm_car_issues"></p>
      </div>
      <a href="#" class="small" onclick="window.appointmentForm.goToStep(3); return false;">Edit</a>
    </div>
  </div>
</div>
```

### Step 4: Extract JavaScript to External File

File: `app/assets/javascripts/appointment_form.js`

```javascript
class AppointmentForm {
  constructor(options = {}) {
    this.accountId = options.accountId;
    this.filterTimeSlots = options.filterTimeSlots;
    this.usePhoneVerification = options.usePhoneVerification;
    this.minimumHours = options.minimumHours || 24;
    this.storeHours = options.storeHours || {};

    this.currentStep = 1;
    this.phoneVerified = false;
    this.selectedExistingVehicle = null;

    this.init();
  }

  init() {
    this.setupEventListeners();
    this.initDatepicker();
    this.setupStepNavigation();
  }

  setupEventListeners() {
    // Service checkboxes
    document.querySelectorAll('.service-checkbox').forEach(checkbox => {
      checkbox.addEventListener('change', () => this.updateServicesSummary());
    });

    // Form field changes
    document.querySelectorAll('input[name^="customer["], select[name^="appointment["]').forEach(field => {
      field.addEventListener('change', () => this.updateConfirmationDisplay(field));
    });

    // Wait/Drop-off
    document.getElementById('wait').addEventListener('change', (e) => {
      document.getElementById('confirm_wait').textContent = e.target.value;
    });

    // Phone verification
    if (this.usePhoneVerification) {
      document.getElementById('verifyPhoneBtn').addEventListener('click', () => {
        this.verifyPhone();
      });
    }

    // Existing vehicles
    if (document.getElementById('existingVehiclesList').children.length > 0) {
      document.querySelectorAll('input[name="vehicle_selection"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
          this.selectExistingVehicle(e.target.value);
        });
      });
      document.getElementById('addNewVehicleBtn').addEventListener('click', () => {
        this.switchToNewVehicle();
      });
    }
  }

  initDatepicker() {
    // Initialize jQuery UI datepicker
    // Implement date selection logic
  }

  setupStepNavigation() {
    // Setup step transitions
  }

  goToStep(step) {
    if (!this.validateStep(this.currentStep)) {
      return false;
    }

    this.currentStep = step;
    this.showStep(step);
    return false;
  }

  showStep(step) {
    // Hide all steps
    document.querySelectorAll('[id^="form-step-"]').forEach(el => {
      el.style.display = 'none';
    });

    // Show selected step
    document.getElementById(`form-step-${step}`).style.display = 'block';

    // Update progress indicator
    this.updateProgressIndicator(step);

    // Update sidebars
    if (step === 4) {
      document.getElementById('summary-sidebar').style.display = 'none';
      document.getElementById('sign-up-sidebar').style.display = 'block';
    } else {
      document.getElementById('sign-up-sidebar').style.display = 'none';
      document.getElementById('summary-sidebar').style.display = 'block';
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  validateStep(step) {
    // Complex validation logic
    // Returns true if valid, false otherwise
  }

  updateConfirmationDisplay(field) {
    // Update confirmation section as user types
  }

  updateServicesSummary() {
    // Update services display
  }

  verifyPhone() {
    // AJAX call to verify phone number
  }

  selectExistingVehicle(vehicleId) {
    // Handle existing vehicle selection
  }

  switchToNewVehicle() {
    // Switch to new vehicle form
  }

  change_location() {
    // Reopen location selection
  }
}
```

---

## Part 5: Risks and Mitigation

### High Risk Areas

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Complex JavaScript Behavior** | CRITICAL | Extract to external file, comprehensive testing, unit tests for validation logic |
| **Form State Management** | HIGH | Use Stimulus controllers or React component for state |
| **AJAX Calls (time slots, phone verify)** | HIGH | Mock endpoints in tests, use fetch API instead of jQuery |
| **Date Validation** | HIGH | Use Rails date validation + JavaScript, test edge cases |
| **Existing Vehicle Lookup** | MEDIUM | Create service for vehicle lookup, test with real data |
| **Phone Verification** | MEDIUM | Create SMS service abstraction, test verification flow |
| **Google Tag Manager** | LOW | Keep GTM code separate, can be added back easily |
| **Accessibility** | MEDIUM | Add ARIA labels, test with screen readers |

---

## Part 6: Implementation Timeline

### Phase 1: Setup & Views (2 weeks)
- Create presenter class
- Create view partials
- Create controller
- Basic HTML structure

### Phase 2: JavaScript & Validation (2 weeks)
- Extract inline JavaScript to Stimulus controller
- Implement step validation
- Implement date picker integration
- Implement form field synchronization

### Phase 3: Services & API Integration (1.5 weeks)
- Create validation services
- Create time slot fetching service
- Create phone verification service
- Create appointment creation service

### Phase 4: Testing & Polish (1.5 weeks)
- Unit tests for services
- Integration tests for form flow
- E2E tests with Capybara
- Performance testing
- Browser compatibility testing

### Phase 5: Rollout (1 week)
- Feature flag configuration
- Beta testing with test account
- Gradual rollout to production
- Monitor error rates
- Collect user feedback

**Total**: 8 weeks for complete migration

---

## Part 7: Conclusion

Block 122 represents **the highest complexity** in PISTN's Block system. Its migration path shows:

1. **Decomposition**: Break monolithic Block into separate concerns (views, controller, services)
2. **Modernization**: Replace inline JavaScript with standard Rails patterns (Stimulus, fetch API)
3. **Testability**: Extract business logic into services that can be tested independently
4. **Maintainability**: Standard Rails conventions make code easier to understand and modify

**Success Criteria**:
- ✅ Feature parity with original Block 122
- ✅ 100% form submission success rate
- ✅ Phone verification flow works
- ✅ Existing vehicle lookup functional
- ✅ All validations pass
- ✅ Performance within 10% of original
- ✅ Accessibility meets WCAG 2.1 AA

**If Block 122 can be migrated successfully, ALL blocks can be migrated.**

---

**Status**: Architectural analysis complete - ready for implementation
**Next Steps**:
1. Create Stimulus controller for form state management
2. Implement form partials with real data
3. Build validation services
4. Begin E2E testing framework

