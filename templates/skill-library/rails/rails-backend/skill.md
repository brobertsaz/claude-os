# Rails Backend Patterns

## Purpose

Provides standard Rails backend patterns including:
- Service objects for business logic
- ActiveRecord best practices
- Migration conventions
- API endpoint patterns
- Background job patterns (Sidekiq)

## Service Object Pattern

All complex business logic should be extracted into service objects:

```ruby
# app/services/user_registration_service.rb
class UserRegistrationService
  def initialize(params)
    @params = params
  end

  def call
    return failure("Email already exists") if User.exists?(email: @params[:email])

    user = User.create!(@params)
    send_welcome_email(user)

    success(user)
  rescue ActiveRecord::RecordInvalid => e
    failure(e.message)
  end

  private

  def send_welcome_email(user)
    UserMailer.welcome(user).deliver_later
  end

  def success(user)
    OpenStruct.new(success?: true, user: user)
  end

  def failure(error)
    OpenStruct.new(success?: false, error: error)
  end
end
```

## ActiveRecord Best Practices

### Query Optimization
```ruby
# Always use includes to prevent N+1 queries
User.includes(:posts, :comments).where(active: true)

# Use find_each for large datasets
User.find_each(batch_size: 1000) do |user|
  process_user(user)
end

# Use select to limit columns
User.select(:id, :name, :email).where(active: true)
```

### Scopes
```ruby
class User < ApplicationRecord
  scope :active, -> { where(active: true) }
  scope :recent, -> { order(created_at: :desc) }
  scope :with_posts, -> { joins(:posts).distinct }
end
```

## Migration Conventions

```ruby
class AddIndexToUsersEmail < ActiveRecord::Migration[7.0]
  disable_ddl_transaction!  # For concurrent indexes

  def change
    add_index :users, :email,
              unique: true,
              algorithm: :concurrently,
              if_not_exists: true
  end
end
```

## API Controller Pattern

```ruby
class Api::V1::UsersController < ApplicationController
  before_action :authenticate_user!
  before_action :set_user, only: [:show, :update, :destroy]

  def index
    @users = User.active.page(params[:page])
    render json: UserSerializer.new(@users).serializable_hash
  end

  def create
    result = UserRegistrationService.new(user_params).call

    if result.success?
      render json: UserSerializer.new(result.user).serializable_hash,
             status: :created
    else
      render json: { error: result.error }, status: :unprocessable_entity
    end
  end

  private

  def set_user
    @user = User.find(params[:id])
  end

  def user_params
    params.require(:user).permit(:name, :email, :password)
  end
end
```

## Background Jobs

```ruby
class ProcessUserReportJob < ApplicationJob
  queue_as :default

  retry_on ActiveRecord::Deadlocked, wait: 5.seconds, attempts: 3
  discard_on ActiveJob::DeserializationError

  def perform(user_id)
    user = User.find(user_id)
    ReportService.new(user).generate
  end
end
```

## Key Principles

1. **Fat models, skinny controllers** - Keep controllers thin
2. **Service objects** - Extract complex logic
3. **Query objects** - For complex database queries
4. **Decorators** - For view-specific logic (use Draper)
5. **Form objects** - For complex form handling
6. **Policy objects** - For authorization (use Pundit)
