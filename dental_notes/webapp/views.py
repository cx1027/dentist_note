from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect

from .speech_to_text import transcript
import json
import os
from .models import Note, AudioRecording, TeethDescription
from members.models import UserActivity

# Create your views here.
@login_required
def speech_index(request):
    note_id = request.GET.get('note_id')
    if note_id:
        try:
            note = Note.objects.get(id=note_id, user=request.user)
            audio_recording = getattr(note, 'audio_recording', None)
            context = {
                'note': {
                    'id': note.id,
                    'title': note.title,
                    'language': note.language,
                    'recording_time': note.recording_time,
                    'transcription': note.transcription,
                    'summary': note.summary,
                    'audio_url': audio_recording.file_path.url if audio_recording else None
                }
            }
            return render(request, 'webapp/speech_index.html', context)
        except Note.DoesNotExist:
            pass
    
    return render(request, 'webapp/speech_index.html')

@login_required
@csrf_exempt  # Only for testing, use proper CSRF protection in production
def start_transcription(request):
    if request.method == 'POST':
        try:
            print("Starting transcription")
            transcript.start_as_transcription()
            print("finish Starting transcription")
            # Your transcription logic here
            return JsonResponse({"status": "success", "message": "Transcription started"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
        
@login_required
@csrf_exempt  # Only for testing, use proper CSRF protection in production
# todo!!! review the process of stop_transcription
def stop_transcription(request):
    if request.method == 'POST':
        try:
            print("Stop transcription")
            transcript.stop_as_transcription()
            audio_url = '/media/recordings/voice.wav'
            print("Audio file path:", audio_url)  # 添加日志
            
            # 确保媒体目录存在
            # recordings_dir = os.path.join(settings.MEDIA_ROOT, 'recordings')
            # os.makedirs(recordings_dir, exist_ok=True)
            
            # 获取音频文件名并构建URL
            # if audio_file_path and os.path.exists(audio_file_path):
            #     audio_filename = os.path.basename(audio_file_path)
            #     audio_url = f'/media/recordings/{audio_filename}'
            #     audio_url = 
            #     print("audio_url:", audio_url)
                
            #     # 将频文件复制到媒体目录
            #     import shutil
            #     destination = os.path.join(recordings_dir, audio_filename)
            #     shutil.copy2(audio_file_path, destination)
            if audio_url:
                return JsonResponse({
                    "status": "success",
                    "message": "Transcription stopped",
                    "audio_url": audio_url
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "message": "Audio file not found"
                })
                
        except Exception as e:
            print("Error in stop_transcription:", str(e))  # 添加错误���志
            return JsonResponse({"status": "error", "message": str(e)})

@login_required
@csrf_exempt
# todo!!!!!diff branches for template or no template
def generate_summary(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from request body
            data = json.loads(request.body)
            text = data.get('text', '')
            
            # Your summary generation logic here
            # summary = f"Summary of: {text}"  # Replace with your actual summary logic
            summary = transcript.meeting_summary_rest(text)
            
            return JsonResponse({
                'success': True,
                'summary': summary
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Only POST method is allowed'
    }, status=405)

@login_required
@csrf_exempt
def generate_template_summary(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from request body
            data = json.loads(request.body)
            template_text = data.get('template_text', '')
            conversation_text = data.get('conversation_text', '')
            
            # Generate summary using your transcript module
            summary = transcript.meeting_template_summary_rest(template_text, conversation_text)
            
            return JsonResponse({
                'success': True,
                'summary': summary
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Only POST method is allowed'
    }, status=405)

@login_required
def history(request):
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'webapp/history.html', {'notes': notes})

@login_required
def note_detail(request, note_id):
    try:
        note = Note.objects.get(id=note_id, user=request.user)
        audio_recording = getattr(note, 'audio_recording', None)
        
        note_data = {
            'id': note.id,
            'title': note.title,
            'created_at': note.created_at.strftime('%Y-%m-%d %H:%M'),
            'language': note.language,
            'recording_time': note.recording_time,
            'transcription': note.transcription,
            'summary': note.summary,
            'audio_url': audio_recording.file_path.url if audio_recording else None
        }
        
        return JsonResponse({
            'success': True,
            'note': note_data
        })
    except Note.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Note not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def template(request):
    # 这里可以处理模板管理逻辑
    return render(request, 'webapp/template.html')

@login_required
def account(request):
    return render(request, 'webapp/account.html')

@login_required
def account_update(request):
    if request.method == 'POST':
        user = request.user
        current_password = request.POST.get('current_password')
        
        # 验证当前密码
        if not current_password or not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect')
            return redirect('account')
        
        # 更新基本信息
        user.email = request.POST.get('email')
        
        # 处理密码更新
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password:
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match')
                return redirect('account')
            user.set_password(new_password)
            # 更新会话，防止用户被登出
            update_session_auth_hash(request, user)
        
        try:
            user.save()
            # 记录账户更新活动
            UserActivity.objects.create(
                user=user,
                activity_type='account_update',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            messages.success(request, 'Account updated successfully')
        except Exception as e:
            messages.error(request, f'Error updating account: {str(e)}')
        
        return redirect('account')
    
    return redirect('account')

@login_required
@csrf_exempt
def save_note(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # 创建笔记
            note = Note.objects.create(
                user=request.user,
                title=data['title'],
                transcription=data['transcription'],
                summary=data.get('summary'),
                language=data['language'],
                recording_time=data['recording_time']
            )

            # 如果音频文件，保存音频记录
            audio_path = os.path.join(settings.MEDIA_ROOT, 'recordings', 'voice.wav')
            if os.path.exists(audio_path):
                # 创建新的文件名
                new_filename = f'recording_{note.id}.wav'
                new_path = os.path.join(settings.MEDIA_ROOT, 'recordings', new_filename)
                
                # 复制文件
                import shutil
                shutil.copy2(audio_path, new_path)
                
                # 创建音频记录
                file_size = os.path.getsize(new_path)
                AudioRecording.objects.create(
                    note=note,
                    file_path=f'recordings/{new_filename}',
                    duration=sum(int(x) * 60 ** i for i, x in enumerate(reversed(data['recording_time'].split(':')))),
                    file_size=file_size
                )

            # 保存牙齿描述
            if 'teeth_description' in data:
                for tooth_num, desc in data['teeth_description'].items():
                    if desc != 'N/A':
                        TeethDescription.objects.create(
                            note=note,
                            tooth_number=int(tooth_num),
                            tooth_name=desc['name'],
                            description=desc['description']
                        )

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Only POST method is allowed'})

@login_required
@csrf_exempt
def update_note(request, note_id):
    if request.method == 'POST':
        try:
            note = Note.objects.get(id=note_id, user=request.user)
            data = json.loads(request.body)
            
            # 更新笔记
            note.title = data['title']
            note.transcription = data['transcription']
            note.summary = data.get('summary')
            note.language = data['language']
            note.recording_time = data['recording_time']
            # 自动更新 updated_at 字段
            note.save()

            return JsonResponse({
                'success': True,
                'updated_at': note.updated_at.strftime('%Y-%m-d %H:%M')
            })
        except Note.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Note not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Only POST method is allowed'})

@login_required
@csrf_exempt
def delete_note(request, note_id):
    if request.method == 'DELETE':
        try:
            note = Note.objects.get(id=note_id, user=request.user)
            # 删除相关的音频文件
            audio_recording = getattr(note, 'audio_recording', None)
            if audio_recording:
                if os.path.exists(audio_recording.file_path.path):
                    os.remove(audio_recording.file_path.path)
            # 删除笔记（这会自动删除相关的 AudioRecording 和 TeethDescription）
            note.delete()
            return JsonResponse({'success': True})
        except Note.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Note not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Only DELETE method is allowed'})
