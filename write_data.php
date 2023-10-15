<?php
// This PHP script receives a POST request and writes its contents to a file.
// A POST request is a method that JavaScript can send data to a web server.
// The POST request must include two things for this PHP script to work:
// - `filename`: specify the full filename of the data being saved
// - `filedata`: contains the full json/csv data to be saved
header('Access-Control-Allow-Origin: mcdermottlab.mit.edu');
if (isset($_POST['filedata']) == true) {
    $filedata = $_POST['filedata'];
} else {
    echo('write_data.php');
    exit;
}
$_POST = filter_input_array(INPUT_POST, FILTER_SANITIZE_STRING); // prevent XSS
if (isset($_POST['filename']) == true) {
    $filename = $_POST['filename'];
} else {
    exit;
}
// Write filedata to filename
file_put_contents($filename, $filedata);
exit;
?>
