# RSpec Testing Patterns

## Purpose

Provides comprehensive RSpec testing patterns for Ruby/Rails applications:
- Unit testing conventions
- Integration testing patterns
- Factory Bot best practices
- Mocking and stubbing
- Test organization

## Test Structure

```ruby
# spec/services/user_registration_service_spec.rb
RSpec.describe UserRegistrationService do
  describe '#call' do
    subject(:service) { described_class.new(params) }

    context 'with valid params' do
      let(:params) { { name: 'Test', email: 'test@example.com', password: 'password123' } }

      it 'creates a user' do
        expect { service.call }.to change(User, :count).by(1)
      end

      it 'returns success' do
        result = service.call
        expect(result).to be_success
        expect(result.user).to be_persisted
      end

      it 'sends welcome email' do
        expect { service.call }
          .to have_enqueued_mail(UserMailer, :welcome)
      end
    end

    context 'with existing email' do
      let(:params) { { name: 'Test', email: existing_user.email, password: 'password123' } }
      let(:existing_user) { create(:user) }

      it 'does not create a user' do
        expect { service.call }.not_to change(User, :count)
      end

      it 'returns failure' do
        result = service.call
        expect(result).not_to be_success
        expect(result.error).to include('Email already exists')
      end
    end
  end
end
```

## Factory Bot Patterns

```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    sequence(:email) { |n| "user#{n}@example.com" }
    name { Faker::Name.name }
    password { 'password123' }

    trait :admin do
      role { :admin }
    end

    trait :with_posts do
      transient do
        posts_count { 3 }
      end

      after(:create) do |user, evaluator|
        create_list(:post, evaluator.posts_count, user: user)
      end
    end
  end
end

# Usage:
create(:user)                     # Basic user
create(:user, :admin)             # Admin user
create(:user, :with_posts)        # User with 3 posts
create(:user, :with_posts, posts_count: 5)  # User with 5 posts
```

## Request Specs (API Testing)

```ruby
# spec/requests/api/v1/users_spec.rb
RSpec.describe 'Api::V1::Users', type: :request do
  describe 'GET /api/v1/users' do
    let!(:users) { create_list(:user, 3) }

    before { get '/api/v1/users', headers: auth_headers }

    it 'returns users' do
      expect(response).to have_http_status(:ok)
      expect(json_response['data'].size).to eq(3)
    end
  end

  describe 'POST /api/v1/users' do
    let(:valid_params) do
      {
        user: {
          name: 'New User',
          email: 'new@example.com',
          password: 'password123'
        }
      }
    end

    context 'with valid params' do
      it 'creates user' do
        expect {
          post '/api/v1/users', params: valid_params, headers: auth_headers
        }.to change(User, :count).by(1)

        expect(response).to have_http_status(:created)
      end
    end
  end
end
```

## Model Specs

```ruby
# spec/models/user_spec.rb
RSpec.describe User, type: :model do
  describe 'validations' do
    subject { build(:user) }

    it { is_expected.to validate_presence_of(:email) }
    it { is_expected.to validate_uniqueness_of(:email).case_insensitive }
    it { is_expected.to validate_presence_of(:name) }
  end

  describe 'associations' do
    it { is_expected.to have_many(:posts).dependent(:destroy) }
    it { is_expected.to have_many(:comments) }
    it { is_expected.to belong_to(:organization).optional }
  end

  describe 'scopes' do
    describe '.active' do
      let!(:active_user) { create(:user, active: true) }
      let!(:inactive_user) { create(:user, active: false) }

      it 'returns only active users' do
        expect(User.active).to contain_exactly(active_user)
      end
    end
  end

  describe '#full_name' do
    let(:user) { build(:user, first_name: 'John', last_name: 'Doe') }

    it 'returns combined name' do
      expect(user.full_name).to eq('John Doe')
    end
  end
end
```

## Shared Examples

```ruby
# spec/support/shared_examples/authenticatable.rb
RSpec.shared_examples 'authenticatable' do
  context 'without authentication' do
    let(:auth_headers) { {} }

    it 'returns unauthorized' do
      subject
      expect(response).to have_http_status(:unauthorized)
    end
  end
end

# Usage in specs:
describe 'GET /api/v1/users' do
  subject { get '/api/v1/users', headers: auth_headers }

  it_behaves_like 'authenticatable'
end
```

## Test Helpers

```ruby
# spec/support/request_helpers.rb
module RequestHelpers
  def json_response
    JSON.parse(response.body)
  end

  def auth_headers
    user = create(:user)
    { 'Authorization' => "Bearer #{user.generate_token}" }
  end
end

RSpec.configure do |config|
  config.include RequestHelpers, type: :request
end
```

## Key Principles

1. **One assertion per test** - Keep tests focused
2. **Use `let` and `let!`** - Lazy vs eager loading
3. **Use `subject`** - Name what you're testing
4. **Use `described_class`** - Reference class being tested
5. **Use traits** - Compose variations cleanly
6. **Avoid database when possible** - Use `build` over `create`
7. **Use `aggregate_failures`** - Group related assertions
