#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>  // or the appropriate message type

class SensorNode : public rclcpp::Node
{
public:
    SensorNode() : Node("sensor_node")
    {
        // Create a publisher that publishes to the "emg_data" topic
        publisher_ = this->create_publisher<std_msgs::msg::String>("emg_data", 10);

        // Create a timer to periodically publish data
        timer_ = this->create_wall_timer(
            std::chrono::seconds(1),  // Adjust the frequency as needed
            std::bind(&SensorNode::publish_data, this)
        );
    }

private:
    void publish_data()
    {
        auto message = std_msgs::msg::String();
        message.data = "EMG data";  // Replace with actual data
        RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str());
        publisher_->publish(message);
    }

    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SensorNode>());
    rclcpp::shutdown();
    return 0;
}