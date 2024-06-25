const menu = document.querySelector('#mobile-menu')
const menuLinks = document.querySelector('.navbar__menu')

menu.addEventListener('click', function() {
    menu.classList.toggle('is-active')
    menuLinks.classList.toggle('active')
})

// Assume jQuery is included elsewhere in your application
function launchProduct(option) {
    var projectName = 'YourProjectName'; // This could also be dynamically set

    $.ajax({
        url: '/launch',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            projectName: projectName,
            option: option
        }),
        success: function(response) {
            alert('Product launched successfully! Instance ID: ' + response.instance_id);
        },
        error: function(error) {
            alert('Failed to launch product. Please try again.');
        }
    });
}
