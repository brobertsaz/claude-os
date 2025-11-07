# Minimal Pistn API Integration Plan for ServiceBot

**Date Created**: 2025-11-06
**Context**: ServiceBot integration with Pistn after Claude OS knowledge export is complete
**Category**: Architecture & Integration
**Status**: Planning - Not Yet Implemented

---

## Current State (November 2025)

### ✅ What's Complete:
1. **Claude OS Export System**: Generic knowledge export to SQLite (format v1.0)
2. **ServiceBot Knowledge Integration**: Embedded RAG engine with vector search
3. **ServiceBot MCP Servers**: 4 servers with 7 tools (currently using stubs)
4. **JavaScript Widget**: Production-ready chat modal for Pistn frontend
5. **Vision Documents**: Claude OS Family established

### ⚠️ What's Stubbed:
- `PistnAPIMCPServer.get_dealer_info()` - Returns fake dealer data
- `ServicesMCPServer.list_services()` - Returns hardcoded services
- `AppointmentsMCPServer.check_availability()` - Returns fake time slots
- `AppointmentsMCPServer.create_appointment()` - Doesn't actually create appointments

### 🎯 The Problem:
**Pistn has NO API endpoints.** ServiceBot can't:
- Get real dealer hours, contact info
- List actual services with real prices
- Check real appointment availability (uses Pistn's complex scheduling logic)
- Create actual appointments (uses Pistn's business rules, validations, callbacks)

---

## The Solution: Three-Phase Minimal API

Build a **minimal, secure API** in Pistn that ServiceBot can call to execute Pistn's business logic.

---

## Phase 1: Test ServiceBot with Knowledge Only (Do This First!)

**Goal**: Validate export + chat widget work before building API

**What to Test**:
1. Export knowledge from Claude OS
2. Import into ServiceBot
3. Add JavaScript widget to Pistn
4. Test knowledge-only conversations

**Commands**:
```bash
# In Claude OS
/claude-os-export dealer_123 --output ./exports

# Copy to ServiceBot
cp claude-os/exports/dealer_123_*.db servicebot/data/dealer_123.db

# Configure ServiceBot .env
KNOWLEDGE_DB_PATH=data/dealer_123.db
ENABLE_KNOWLEDGE_SEARCH=true
KNOWLEDGE_USE_EMBEDDINGS=true
OPENAI_API_KEY=your_key

# Deploy ServiceBot
cd servicebot
docker-compose up -d

# Add widget to Pistn layout
# (see implementation below)
```

**Test Conversations** (knowledge-only):
- "What are your hours?" ✅ (from knowledge base)
- "How long does an oil change take?" ✅ (from knowledge base)
- "What's your cancellation policy?" ✅ (from knowledge base)
- "I want to book an appointment" ⚠️ (will fail gracefully - no API yet)

**Success Criteria**:
- Widget loads on Pistn
- Knowledge queries work
- Responses stream properly
- Graceful degradation when tools not available

**Pistn Changes** (Minimal):
```ruby
# app/views/layouts/application.html.erb (or dealer layout)
<% if ENV['SERVICEBOT_ENABLED'] == 'true' %>
  <script src="<%= ENV['SERVICEBOT_URL'] %>/static/servicebot-widget.js"></script>
  <script>
    ServiceBotWidget.init({
      apiUrl: '<%= ENV['SERVICEBOT_URL'] %>',
      dealerId: '<%= current_account.id if current_account.is_a?(DealerAccount) %>',
      primaryColor: '<%= current_account.primary_bg if current_account.is_a?(DealerAccount) %>',
      greeting: 'Hi! How can we help you today?'
    });
  </script>
<% end %>
```

**Duration**: 1-2 days (testing and validation)

---

## Phase 2: Add Minimal Read-Only API (After Phase 1 Works)

**Goal**: Replace stubs with real Pistn data (no writes yet)

### Implementation

#### 2.1: Create API Controller

```ruby
# pistn/app/controllers/api/v1/servicebot_controller.rb
module Api
  module V1
    class ServicebotController < ApplicationController
      skip_before_action :verify_authenticity_token
      before_action :authenticate_servicebot

      # GET /api/v1/servicebot/dealers/:id
      def dealer_info
        dealer = DealerAccount.find(params[:id])

        render json: {
          id: dealer.id,
          name: dealer.name,
          address: dealer.full_address,
          city: dealer.city,
          state: dealer.state,
          zip: dealer.zip,
          phone: dealer.phone,
          email: dealer.email,
          hours: build_hours_hash(dealer)
        }
      rescue ActiveRecord::RecordNotFound
        render json: { error: 'Dealer not found' }, status: 404
      end

      # GET /api/v1/servicebot/dealers/:dealer_id/services
      def services
        dealer = DealerAccount.find(params[:dealer_id])

        # Adjust based on Pistn's actual service model
        services = dealer.oil_change_services || []

        render json: services.map { |service| {
          id: service.id,
          name: service.name,
          description: service.description || '',
          price: service.price,
          duration_minutes: service.duration_minutes || 60
        }}
      end

      private

      def authenticate_servicebot
        api_key = request.headers['X-ServiceBot-API-Key']

        unless api_key.present? && api_key == ENV['SERVICEBOT_API_KEY']
          render json: { error: 'Unauthorized' }, status: 401
        end
      end

      def build_hours_hash(dealer)
        # Adjust based on how Pistn stores hours
        {
          monday: dealer.monday_hours || 'Closed',
          tuesday: dealer.tuesday_hours || 'Closed',
          wednesday: dealer.wednesday_hours || 'Closed',
          thursday: dealer.thursday_hours || 'Closed',
          friday: dealer.friday_hours || 'Closed',
          saturday: dealer.saturday_hours || 'Closed',
          sunday: dealer.sunday_hours || 'Closed'
        }
      end
    end
  end
end
```

#### 2.2: Add Routes

```ruby
# pistn/config/routes.rb
namespace :api do
  namespace :v1 do
    scope :servicebot do
      get 'dealers/:id', to: 'servicebot#dealer_info'
      get 'dealers/:dealer_id/services', to: 'servicebot#services'
    end
  end
end
```

#### 2.3: Update ServiceBot MCP Servers

```python
# servicebot/app/mcp_servers/pistn_api.py
class PistnAPIMCPServer:
    def __init__(self):
        self.base_url = settings.PISTN_API_URL  # e.g., http://localhost:3000
        self.api_key = settings.PISTN_API_KEY
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-ServiceBot-API-Key": self.api_key,
                "Content-Type": "application/json"
            },
            timeout=10.0
        )

    async def get_dealer_info(self, dealer_id: str) -> Dict[str, Any]:
        """Get real dealer data from Pistn API."""
        try:
            response = await self.client.get(f"/api/v1/servicebot/dealers/{dealer_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get dealer info: {e}")
            # Fallback to stub for graceful degradation
            return self._stub_dealer_info(dealer_id)

# servicebot/app/mcp_servers/services.py
class ServicesMCPServer:
    async def list_services(self, dealer_id: str) -> Dict[str, Any]:
        """Get real services from Pistn API."""
        try:
            response = await self.pistn_client.get(
                f"/api/v1/servicebot/dealers/{dealer_id}/services"
            )
            response.raise_for_status()
            services = response.json()

            return {
                "success": True,
                "services": services,
                "count": len(services)
            }
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return {"success": False, "services": [], "count": 0}
```

#### 2.4: Configuration

**Pistn `.env`**:
```bash
# ServiceBot Integration
SERVICEBOT_ENABLED=true
SERVICEBOT_URL=http://localhost:8000  # or production URL
SERVICEBOT_API_KEY=your_secure_random_key_here  # Generate with: SecureRandom.hex(32)
```

**ServiceBot `.env`**:
```bash
# Pistn API Integration
PISTN_API_URL=http://localhost:3000  # or production Pistn URL
PISTN_API_KEY=same_key_as_above
```

**Test**:
```bash
# Test Pistn API directly
curl -H "X-ServiceBot-API-Key: your_key" \
  http://localhost:3000/api/v1/servicebot/dealers/123

# Test in ServiceBot
# Should now return real dealer data instead of stubs
```

**Duration**: 2-3 days (implementation + testing)

---

## Phase 3: Add Appointment Booking (After Phase 2 Works)

**Goal**: Enable full appointment booking through ServiceBot

### 3.1: Identify Pistn's Appointment Logic

**Before implementing**, answer these questions:
- What model handles appointments? (e.g., `Appointment`, `ServiceAppointment`)
- What service/class creates appointments? (e.g., `AppointmentCreationService`)
- What validates availability? (e.g., `AppointmentAvailabilityService`, `BlockScheduler`)
- What are required fields? (customer info, vehicle, service, time)
- What validations exist? (blackout dates, capacity, dealer hours)
- What side effects happen? (emails, SMS, calendar updates)

### 3.2: Add Appointment Endpoints

```ruby
# pistn/app/controllers/api/v1/servicebot_controller.rb

# POST /api/v1/servicebot/dealers/:dealer_id/appointments/check_availability
def check_availability
  dealer = DealerAccount.find(params[:dealer_id])
  date = Date.parse(params[:date])
  service_id = params[:service_id]

  # Use existing Pistn service (adjust to actual service name)
  availability = AppointmentAvailabilityService.new(
    dealer: dealer,
    date: date,
    service_id: service_id
  ).call

  render json: {
    success: true,
    date: date,
    slots: availability.map { |slot| {
      time: slot.time.iso8601,
      available: slot.available,
      capacity: slot.capacity
    }}
  }
rescue => e
  render json: { success: false, error: e.message }, status: 422
end

# POST /api/v1/servicebot/dealers/:dealer_id/appointments
def create_appointment
  dealer = DealerAccount.find(params[:dealer_id])

  # Use existing Pistn service (adjust to actual service name)
  result = AppointmentCreationService.new(
    dealer: dealer,
    customer_name: params[:customer_name],
    customer_email: params[:customer_email],
    customer_phone: params[:customer_phone],
    service_id: params[:service_id],
    appointment_time: Time.parse(params[:appointment_time]),
    vehicle_year: params.dig(:vehicle, :year),
    vehicle_make: params.dig(:vehicle, :make),
    vehicle_model: params.dig(:vehicle, :model),
    notes: params[:notes]
  ).call

  if result.success?
    render json: {
      success: true,
      appointment: {
        id: result.appointment.id,
        confirmation_number: result.appointment.confirmation_number,
        scheduled_time: result.appointment.scheduled_time.iso8601
      }
    }
  else
    render json: {
      success: false,
      errors: result.errors
    }, status: 422
  end
rescue => e
  render json: { success: false, error: e.message }, status: 500
end
```

### 3.3: Add Routes

```ruby
# pistn/config/routes.rb
namespace :api do
  namespace :v1 do
    scope :servicebot do
      # ... existing routes ...
      post 'dealers/:dealer_id/appointments/check_availability',
           to: 'servicebot#check_availability'
      post 'dealers/:dealer_id/appointments',
           to: 'servicebot#create_appointment'
    end
  end
end
```

### 3.4: Update ServiceBot MCP Server

```python
# servicebot/app/mcp_servers/appointments.py
class AppointmentsMCPServer:
    async def check_availability(
        self,
        dealer_id: str,
        date: str,
        service_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check real appointment availability via Pistn API."""
        try:
            response = await self.pistn_client.post(
                f"/api/v1/servicebot/dealers/{dealer_id}/appointments/check_availability",
                json={"date": date, "service_id": service_id}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Availability check failed: {e}")
            return {"success": False, "error": str(e)}

    async def create_appointment(
        self,
        dealer_id: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        service_id: str,
        appointment_time: str,
        vehicle: Dict[str, str],
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create real appointment via Pistn API."""
        try:
            response = await self.pistn_client.post(
                f"/api/v1/servicebot/dealers/{dealer_id}/appointments",
                json={
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "customer_phone": customer_phone,
                    "service_id": service_id,
                    "appointment_time": appointment_time,
                    "vehicle": vehicle,
                    "notes": notes
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Appointment creation failed: {e}")
            return {"success": False, "error": str(e)}
```

**Duration**: 3-5 days (complex, needs thorough testing)

---

## Security Considerations

### API Key Generation
```ruby
# Generate secure API key
SecureRandom.hex(32)
# => "a1b2c3d4e5f6..."
```

### Rate Limiting (Optional but Recommended)
```ruby
# Gemfile
gem 'rack-attack'

# config/initializers/rack_attack.rb
Rack::Attack.throttle('servicebot/ip', limit: 100, period: 1.minute) do |req|
  if req.path.start_with?('/api/v1/servicebot')
    req.ip
  end
end
```

### HTTPS in Production
- ServiceBot MUST use HTTPS (WebSocket requires it)
- Pistn API should use HTTPS for security
- Set `PISTN_API_URL=https://pistn.yourdomain.com` in production

---

## Testing Strategy

### Phase 1 Testing
- [ ] Export knowledge from Claude OS
- [ ] Import into ServiceBot successfully
- [ ] Widget loads on Pistn page
- [ ] Can ask knowledge questions
- [ ] Streaming responses work
- [ ] Conversation persists in localStorage

### Phase 2 Testing
- [ ] API authentication works
- [ ] Can get real dealer info
- [ ] Can list real services
- [ ] Graceful fallback if API fails
- [ ] Error handling works

### Phase 3 Testing
- [ ] Can check availability for real dates
- [ ] Can create actual appointments
- [ ] Appointments appear in Pistn dashboard
- [ ] Customer receives confirmation
- [ ] All validations work (capacity, hours, etc.)
- [ ] Error messages are user-friendly

---

## Deployment Checklist

### ServiceBot Deployment
- [ ] Docker container running
- [ ] Knowledge DB imported
- [ ] HTTPS/SSL configured
- [ ] CORS configured for Pistn domain
- [ ] Environment variables set
- [ ] Widget file served at `/static/servicebot-widget.js`

### Pistn Deployment
- [ ] API controller added
- [ ] Routes configured
- [ ] API key set in `.env`
- [ ] Widget script added to layout
- [ ] ServiceBot enabled flag set
- [ ] CORS headers configured (if needed)

---

## Monitoring & Maintenance

### Logs to Watch
**ServiceBot**:
- WebSocket connections
- MCP tool calls
- API call failures
- Knowledge query performance

**Pistn**:
- ServiceBot API requests
- Authentication failures
- Appointment creation errors

### Metrics to Track
- Conversations started
- Messages sent
- Knowledge queries performed
- Appointments booked via chat
- API response times
- Error rates

---

## Future Enhancements

### Post-MVP Features
- [ ] Customer authentication (lookup by email/phone)
- [ ] Appointment rescheduling
- [ ] Appointment cancellation
- [ ] Service history lookup
- [ ] Vehicle history integration
- [ ] Multi-language support
- [ ] Voice integration
- [ ] SMS integration

### Knowledge Base Updates
- [ ] Sync `enhanced_documentation_service.rb` knowledge to Claude OS
- [ ] Regular export/import workflow
- [ ] Automated knowledge updates

---

## Rollback Plan

If something breaks:

1. **Phase 1 Issues**: Disable widget
   ```ruby
   # .env
   SERVICEBOT_ENABLED=false
   ```

2. **Phase 2 Issues**: ServiceBot falls back to stubs automatically

3. **Phase 3 Issues**: Disable appointment booking tool
   ```python
   # servicebot/app/mcp_servers/appointments.py
   self.enabled = False
   ```

---

## Key Takeaways

✅ **Start minimal** - Test knowledge-only first
✅ **Phased approach** - Build API incrementally
✅ **Reuse Pistn logic** - Don't duplicate business rules
✅ **Graceful degradation** - Stubs as fallbacks
✅ **Security first** - API key authentication
✅ **Test thoroughly** - Each phase validated before next

---

## Related Documentation

- [ServiceBot README](servicebot/README.md)
- [Pistn Integration Guide](servicebot/integrations/PISTN_INTEGRATION.md)
- [Knowledge Integration](servicebot/docs/KNOWLEDGE_INTEGRATION.md)
- [Claude OS Family](claude-os/docs/CLAUDE_OS_FAMILY.md)
- [Export Format Spec](claude-os/docs/EXPORT_FORMAT_SPEC.md)

---

**Next Action**: Run Phase 1 to test ServiceBot with knowledge-only conversations!
