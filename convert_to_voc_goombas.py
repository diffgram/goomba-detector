from play.diffgram_autogluon_converter import coco2voc

annotations_file = '/home/pablo/Dropbox/diffgram/ai_vision/prototype/app/play/diffgram_autogluon_converter/goombas_training_coco.json'
labels_target_folder = '/home/pablo/Dropbox/diffgram/ai_vision/prototype/app/play/diffgram_autogluon_converter/voc_data_train'
data_folder = '/home/pablo/Dropbox/diffgram/ai_vision/prototype/app/play/diffgram_autogluon_converter/images'

coco2voc.coco2voc(annotations_file, labels_target_folder, n=189)